"""
Universal File Ingestion & CSV Converter Engine.
Accepts any file format (Excel, JSON, Parquet, XML, HTML, SQLite, Logs, Documents, Binaries),
converts data into clean structured CSV format, and persists files with SQLite audit registry.
"""

import os
import io
import re
import csv
import json
import uuid
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd


class UniversalFileConverter:
    """Universal engine that converts any incoming file format into standard CSV."""

    def __init__(self, db_path: str = "database/maintenance.db", output_dir: str = "data/converted"):
        self.db_path = db_path
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self._ensure_database()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_database(self):
        """Ensure uploaded_files metadata table exists in SQLite."""
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS uploaded_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id TEXT UNIQUE NOT NULL,
                    original_filename TEXT NOT NULL,
                    file_format TEXT NOT NULL,
                    original_size_bytes INTEGER NOT NULL,
                    converted_csv_filename TEXT NOT NULL,
                    converted_csv_path TEXT NOT NULL,
                    row_count INTEGER NOT NULL DEFAULT 0,
                    column_count INTEGER NOT NULL DEFAULT 0,
                    columns_json TEXT,
                    upload_timestamp TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'completed'
                )
            """)
            conn.commit()

    def convert_and_store(self, file_bytes: bytes, original_filename: str) -> Dict[str, Any]:
        """
        Accepts any file's raw bytes and filename, converts content to a DataFrame,
        saves to CSV in data/converted/, records metadata in SQLite, and returns details.
        """
        file_id = uuid.uuid4().hex[:12]
        size_bytes = len(file_bytes)
        ext = os.path.splitext(original_filename)[1].lower()
        if not ext:
            ext = ".unknown"

        # Attempt format-specific parsing with progressive graceful fallbacks
        df = self._parse_file_to_dataframe(file_bytes, ext, original_filename)

        if df is None or df.empty:
            # Fallback to text lines or binary inspection so conversion never fails
            df = self._parse_as_raw_fallback(file_bytes, original_filename)

        # Sanitize column names
        df.columns = [str(c).strip().replace("\n", " ").replace("\r", "") for c in df.columns]

        # Generate unique CSV filename and target path
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = re.sub(r'[^a-zA-Z0-9_-]', '_', os.path.splitext(original_filename)[0])[:30]
        converted_filename = f"{base_name}_{timestamp_str}_{file_id}.csv"
        converted_path = os.path.join(self.output_dir, converted_filename)

        # Persist CSV to disk
        df.to_csv(converted_path, index=False, encoding="utf-8")

        row_count = int(len(df))
        col_count = int(len(df.columns))
        columns_list = list(df.columns)
        columns_json = json.dumps(columns_list)
        now_iso = datetime.now().isoformat()

        # Save metadata to database
        with self._get_connection() as conn:
            conn.execute(
                """INSERT INTO uploaded_files 
                   (file_id, original_filename, file_format, original_size_bytes, 
                    converted_csv_filename, converted_csv_path, row_count, column_count, 
                    columns_json, upload_timestamp, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (file_id, original_filename, ext, size_bytes, converted_filename,
                 converted_path, row_count, col_count, columns_json, now_iso, "completed")
            )
            conn.commit()

        # Preview records (up to 15 rows)
        preview_records = df.head(15).replace({float("nan"): None}).to_dict(orient="records")

        return {
            "file_id": file_id,
            "original_filename": original_filename,
            "file_format": ext,
            "original_size_bytes": size_bytes,
            "converted_csv_filename": converted_filename,
            "converted_csv_path": converted_path,
            "row_count": row_count,
            "column_count": col_count,
            "columns": columns_list,
            "upload_timestamp": now_iso,
            "status": "completed",
            "preview": preview_records,
            "dataframe": df
        }

    def _parse_file_to_dataframe(self, file_bytes: bytes, ext: str, filename: str) -> Optional[pd.DataFrame]:
        """Dispatches to the appropriate parser based on extension and content."""
        try:
            # 1. Excel Spreadsheets
            if ext in [".xlsx", ".xls", ".xlsm", ".xlsb", ".ods"]:
                return self._parse_excel(file_bytes)

            # 2. JSON / JSON Lines
            if ext in [".json", ".jsonl", ".ndjson"]:
                return self._parse_json(file_bytes)

            # 3. Parquet / Feather
            if ext in [".parquet", ".pq"]:
                return pd.read_parquet(io.BytesIO(file_bytes))
            if ext in [".feather"]:
                return pd.read_feather(io.BytesIO(file_bytes))

            # 4. Delimited Text (CSV, TSV, PSV)
            if ext in [".csv", ".tsv", ".tab", ".psv"]:
                return self._parse_delimited(file_bytes)

            # 5. Log Files
            if ext in [".log"]:
                return self._parse_logs(file_bytes)

            # 6. XML / HTML
            if ext in [".xml"]:
                try:
                    return pd.read_xml(io.BytesIO(file_bytes))
                except Exception:
                    pass
            if ext in [".html", ".htm"]:
                tables = pd.read_html(io.BytesIO(file_bytes))
                if tables:
                    return tables[0]

            # 7. SQLite DB file
            if ext in [".db", ".sqlite", ".sqlite3"]:
                return self._parse_sqlite_db(file_bytes)

            # 8. Plain text & structured config (txt, yaml, yml, ini, env, md)
            if ext in [".txt", ".yaml", ".yml", ".ini", ".conf", ".env", ".md", ".rst"]:
                # Try delimited parse first in case it's a disguised CSV/TSV
                try:
                    df = self._parse_delimited(file_bytes)
                    if df is not None and len(df.columns) > 1 and len(df) > 0:
                        return df
                except Exception:
                    pass
                return self._parse_text_lines(file_bytes)

        except Exception:
            # Silently fall back to next handler
            pass

        return None

    def _parse_excel(self, file_bytes: bytes) -> pd.DataFrame:
        """Parse Excel workbook, combining multiple sheets or extracting the primary sheet."""
        excel_file = io.BytesIO(file_bytes)
        sheets_dict = pd.read_excel(excel_file, sheet_name=None)
        if not sheets_dict:
            return pd.DataFrame()

        combined_dfs = []
        for sheet_name, sheet_df in sheets_dict.items():
            if not sheet_df.empty:
                sheet_df = sheet_df.copy()
                if len(sheets_dict) > 1:
                    sheet_df.insert(0, "_sheet_name", sheet_name)
                combined_dfs.append(sheet_df)

        if combined_dfs:
            return pd.concat(combined_dfs, ignore_index=True)
        return pd.DataFrame()

    def _parse_json(self, file_bytes: bytes) -> pd.DataFrame:
        """Parse JSON or JSONL into tabular DataFrame, flattening nested structures."""
        text = file_bytes.decode("utf-8", errors="ignore").strip()
        if not text:
            return pd.DataFrame()

        # Check if JSONL (newline-delimited)
        if "\n" in text and not text.startswith("["):
            lines = [json.loads(line) for line in text.splitlines() if line.strip()]
            if lines:
                return pd.json_normalize(lines)

        data = json.loads(text)
        if isinstance(data, list):
            return pd.json_normalize(data)
        elif isinstance(data, dict):
            # Check for common envelope keys containing array of records
            for key in ["data", "records", "items", "readings", "results", "telemetry", "rows"]:
                if key in data and isinstance(data[key], list) and len(data[key]) > 0:
                    return pd.json_normalize(data[key])
            # Flatten the single dictionary into a 1-row table
            return pd.json_normalize(data)

        return pd.DataFrame([{"raw_json_value": str(data)}])

    def _parse_delimited(self, file_bytes: bytes) -> pd.DataFrame:
        """Auto-detect delimiter and parse CSV/TSV/PSV."""
        sample = file_bytes[:8192].decode("utf-8", errors="ignore")
        delimiter = None
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=[",", "\t", ";", "|"])
            delimiter = dialect.delimiter
        except Exception:
            # Fallback heuristic
            for cand in [",", "\t", ";", "|"]:
                if cand in sample:
                    delimiter = cand
                    break

        return pd.read_csv(
            io.BytesIO(file_bytes),
            sep=delimiter or ",",
            engine="python",
            on_bad_lines="skip"
        )

    def _parse_logs(self, file_bytes: bytes) -> pd.DataFrame:
        """Parse server/sensor logs into structured columns: timestamp, level, component, message."""
        text = file_bytes.decode("utf-8", errors="ignore")
        lines = [l for l in text.splitlines() if l.strip()]
        if not lines:
            return pd.DataFrame()

        records = []
        # Regex to detect ISO/standard timestamp and log levels
        ts_regex = re.compile(r"(\d{4}[-/.]\d{2}[-/.]\d{2}[T\s]\d{2}:\d{2}:\d{2}(?:\.\d+)?)")
        lvl_regex = re.compile(r"\b(DEBUG|INFO|NOTICE|WARN|WARNING|ERROR|CRITICAL|FATAL)\b", re.IGNORECASE)

        for i, line in enumerate(lines, start=1):
            ts_match = ts_regex.search(line)
            lvl_match = lvl_regex.search(line)

            ts_val = ts_match.group(1) if ts_match else None
            lvl_val = lvl_match.group(1).upper() if lvl_match else "INFO"

            # Clean message
            msg = line
            if ts_match:
                msg = msg.replace(ts_match.group(0), "")
            if lvl_match:
                msg = msg.replace(lvl_match.group(0), "")
            msg = msg.strip(" -:[]|")

            records.append({
                "line_number": i,
                "timestamp": ts_val or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "log_level": lvl_val,
                "message": msg or line
            })

        return pd.DataFrame(records)

    def _parse_sqlite_db(self, file_bytes: bytes) -> pd.DataFrame:
        """Extract all tables from an uploaded SQLite database file."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            conn = sqlite3.connect(tmp_path)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [r[0] for r in cursor.fetchall()]

            dfs = []
            for t in tables:
                tdf = pd.read_sql_query(f"SELECT * FROM `{t}`", conn)
                if not tdf.empty:
                    tdf.insert(0, "_source_table", t)
                    dfs.append(tdf)
            conn.close()

            if dfs:
                return pd.concat(dfs, ignore_index=True)
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

        return pd.DataFrame()

    def _parse_text_lines(self, file_bytes: bytes) -> pd.DataFrame:
        """Parse unstructured text documents into indexed paragraphs/lines."""
        text = file_bytes.decode("utf-8", errors="ignore")
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if not lines:
            return pd.DataFrame([{"line_number": 1, "content": "", "character_count": 0}])

        return pd.DataFrame([
            {
                "line_number": idx + 1,
                "content": line,
                "character_count": len(line)
            }
            for idx, line in enumerate(lines)
        ])

    def _parse_as_raw_fallback(self, file_bytes: bytes, filename: str) -> pd.DataFrame:
        """
        Universal fallback: converts binary or unknown content into hex & ASCII chunk records.
        Guarantees that ANY file can be successfully converted into a valid CSV.
        """
        # First check if decodeable as readable text
        try:
            text = file_bytes.decode("utf-8", errors="strict")
            lines = [l for l in text.splitlines() if l.strip()]
            if lines:
                return pd.DataFrame([
                    {"line_number": i + 1, "text_content": line, "length_bytes": len(line.encode("utf-8"))}
                    for i, line in enumerate(lines[:10000])
                ])
        except Exception:
            pass

        # Binary chunk segmentation (64 bytes per row)
        chunk_size = 64
        records = []
        total_chunks = min(len(file_bytes) // chunk_size + 1, 5000)

        for i in range(total_chunks):
            offset = i * chunk_size
            chunk = file_bytes[offset:offset + chunk_size]
            if not chunk:
                break
            hex_str = chunk.hex(" ").upper()
            ascii_str = "".join(chr(b) if 32 <= b <= 126 else "." for b in chunk)
            records.append({
                "chunk_index": i + 1,
                "byte_offset": f"0x{offset:06X}",
                "byte_length": len(chunk),
                "ascii_preview": ascii_str,
                "hex_data": hex_str
            })

        return pd.DataFrame(records)

    # ------------------ REGISTRY & UTILITY QUERIES ------------------

    def list_converted_files(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List previously converted files stored in database and verify their existence."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT id, file_id, original_filename, file_format, original_size_bytes,
                          converted_csv_filename, converted_csv_path, row_count, column_count,
                          columns_json, upload_timestamp, status
                   FROM uploaded_files
                   ORDER BY upload_timestamp DESC
                   LIMIT ?""",
                (limit,)
            )
            rows = cursor.fetchall()

        results = []
        for r in rows:
            d = dict(r)
            d["exists_on_disk"] = os.path.exists(d["converted_csv_path"])
            try:
                d["columns"] = json.loads(d["columns_json"]) if d["columns_json"] else []
            except Exception:
                d["columns"] = []
            results.append(d)
        return results

    def get_converted_file(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Fetch metadata and DataFrame for a specific file_id."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT * FROM uploaded_files WHERE file_id = ?""",
                (file_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            d = dict(row)

        if os.path.exists(d["converted_csv_path"]):
            d["dataframe"] = pd.read_csv(d["converted_csv_path"])
        else:
            d["dataframe"] = None
        return d

    def delete_converted_file(self, file_id: str) -> bool:
        """Deletes CSV file from storage and database registry."""
        file_meta = self.get_converted_file(file_id)
        if not file_meta:
            return False

        csv_path = file_meta.get("converted_csv_path")
        if csv_path and os.path.exists(csv_path):
            try:
                os.remove(csv_path)
            except Exception:
                pass

        with self._get_connection() as conn:
            conn.execute("DELETE FROM uploaded_files WHERE file_id = ?", (file_id,))
            conn.commit()
        return True

    def get_ingestion_stats(self) -> Dict[str, Any]:
        """Aggregate summary metrics of all ingested files."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as total_files,
                       COALESCE(SUM(original_size_bytes), 0) as total_size_bytes,
                       COALESCE(SUM(row_count), 0) as total_rows
                FROM uploaded_files
            """)
            summary = dict(cursor.fetchone() or {})

        total_files = summary.get("total_files", 0)
        total_size = summary.get("total_size_bytes", 0)
        total_rows = summary.get("total_rows", 0)

        # Calculate directory storage footprint
        disk_bytes = 0
        if os.path.exists(self.output_dir):
            for f in os.listdir(self.output_dir):
                fp = os.path.join(self.output_dir, f)
                if os.path.isfile(fp):
                    disk_bytes += os.path.getsize(fp)

        return {
            "total_files": total_files,
            "total_rows": total_rows,
            "total_original_size_bytes": total_size,
            "total_csv_disk_bytes": disk_bytes,
            "storage_formatted": f"{disk_bytes / (1024 * 1024):.2f} MB" if disk_bytes > 1024 * 1024 else f"{disk_bytes / 1024:.1f} KB"
        }
