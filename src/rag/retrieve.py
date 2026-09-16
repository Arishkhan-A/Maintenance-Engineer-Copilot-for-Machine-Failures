"""RAG Vector Retrieval with metadata filtering, relevance scoring, and machine theory search."""
import json
import os
import re
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.rag.ingest import build_knowledge_index

class KnowledgeRetriever:
    """Semantic and keyword-hybrid retriever for industrial technical manuals and engineering theory."""

    def __init__(self, index_path: str = "database/rag_index.json", docs_dir: str = "documents"):
        self.index_path = index_path
        self.docs_dir = docs_dir
        self.chunks: List[Dict[str, Any]] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self._load_or_build()

    def reload_index(self):
        """Force reloads the JSON index and re-computes TF-IDF matrix."""
        self._load_or_build()

    def _load_or_build(self):
        if not os.path.exists(self.index_path):
            self.chunks = build_knowledge_index(self.docs_dir, self.index_path)
        else:
            try:
                with open(self.index_path, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
            except Exception:
                self.chunks = build_knowledge_index(self.docs_dir, self.index_path)

        if not self.chunks:
            return

        corpus = [f"{c['header']} {c['text']} {' '.join(c.get('tags', []))} {' '.join(c.get('applicable_machines', []))}" for c in self.chunks]
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", max_features=10000)
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        machine_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant document passages with cosine similarity and keyword boosting.
        Applies metadata filtering when category, tag, or machine_type is provided.
        """
        if not self.chunks or self.vectorizer is None or self.tfidf_matrix is None:
            self._load_or_build()
        if not self.chunks:
            return []

        # Vector score
        q_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(q_vec, self.tfidf_matrix)[0]

        q_lower = query.lower()
        query_words = [w for w in re.findall(r"\w+", q_lower) if len(w) > 3]

        results = []
        for idx, chunk in enumerate(self.chunks):
            score = float(scores[idx])

            # Apply category filter
            if category and chunk.get("category") != category:
                continue

            # Apply tag filter
            if tag and tag.lower() not in [t.lower() for t in chunk.get("tags", [])]:
                score *= 0.5

            # Machine type relevance boost
            applicable = [m.lower() for m in chunk.get("applicable_machines", [])]
            if machine_type and any(machine_type.lower() in app for app in applicable):
                score += 0.15

            # Keyword presence bonus
            chunk_text_lower = chunk["text"].lower()
            for word in query_words:
                if word in chunk_text_lower:
                    score += 0.06
                if word in chunk.get("header", "").lower():
                    score += 0.10

            results.append({
                "chunk_id": chunk["chunk_id"],
                "source_file": chunk["source_file"],
                "category": chunk.get("category", "manual"),
                "header": chunk["header"],
                "text": chunk["text"],
                "score": round(score, 4),
                "tags": chunk.get("tags", []),
                "applicable_machines": chunk.get("applicable_machines", [])
            })

        # Rank by score descending
        results = sorted(results, key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def search_theory(
        self,
        query: str,
        top_k: int = 3,
        machine_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Specialized retrieval for engineering machine theory, working principles,
        physics laws, equations, and failure progression.
        """
        # First attempt with category="theory"
        theory_res = self.retrieve(query, top_k=top_k, category="theory", machine_type=machine_type)
        if len(theory_res) >= top_k:
            return theory_res

        # If not enough theory chunks, supplement with manuals / troubleshooting
        all_res = self.retrieve(query, top_k=top_k, machine_type=machine_type)
        combined = {r["chunk_id"]: r for r in theory_res}
        for r in all_res:
            if r["chunk_id"] not in combined:
                combined[r["chunk_id"]] = r
            if len(combined) >= top_k:
                break
        return list(combined.values())[:top_k]


if __name__ == "__main__":
    retriever = KnowledgeRetriever()
    test_res = retriever.retrieve("vibration bearing overheating M17", top_k=2)
    print("Retrieved test items:", len(test_res))
    for r in test_res:
        print(f"[{r['source_file']}] {r['header']} (Score: {r['score']})")

    theory_res = retriever.search_theory("centrifugal pump cavitation NPSH Bernoulli", top_k=2)
    print("\nRetrieved theory items:", len(theory_res))
    for r in theory_res:
        print(f"[{r['source_file']}] {r['header']} (Score: {r['score']})")
