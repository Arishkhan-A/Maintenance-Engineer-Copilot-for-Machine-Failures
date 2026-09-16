"""Unit tests for UniversalFileConverter engine."""
import os
import io
import json
import pytest
import pandas as pd
from src.utils.file_converter import UniversalFileConverter

@pytest.fixture
def converter(tmp_path):
    db_file = str(tmp_path / "test_maintenance.db")
    out_dir = str(tmp_path / "converted_csv")
    return UniversalFileConverter(db_path=db_file, output_dir=out_dir)

def test_convert_json(converter):
    data = [
        {"machine_id": "M01", "temperature": 75.4, "status": "Normal"},
        {"machine_id": "M02", "temperature": 88.1, "status": "High"}
    ]
    json_bytes = json.dumps(data).encode("utf-8")
    result = converter.convert_and_store(json_bytes, "fleet_telemetry.json")

    assert result["status"] == "completed"
    assert result["row_count"] == 2
    assert result["column_count"] >= 3
    assert os.path.exists(result["converted_csv_path"])

    # Read back CSV
    df = pd.read_csv(result["converted_csv_path"])
    assert len(df) == 2
    assert "machine_id" in df.columns

def test_convert_delimited_csv(converter):
    csv_content = b"timestamp,rpm,vibration\n2026-09-11 10:00:00,1800,2.1\n2026-09-11 10:01:00,1820,2.4\n"
    result = converter.convert_and_store(csv_content, "readings.csv")

    assert result["row_count"] == 2
    assert "rpm" in result["columns"]
    assert os.path.exists(result["converted_csv_path"])

def test_convert_log_file(converter):
    log_content = b"2026-09-11 12:00:01 INFO System startup completed\n2026-09-11 12:00:05 ERROR Bearing vibration exceeded threshold 4.5 mm/s\n"
    result = converter.convert_and_store(log_content, "system.log")

    assert result["row_count"] == 2
    df = pd.read_csv(result["converted_csv_path"])
    assert "log_level" in df.columns
    assert "message" in df.columns
    assert df.iloc[1]["log_level"] == "ERROR"

def test_convert_excel(converter):
    # Create excel in-memory
    df_orig = pd.DataFrame({"asset": ["Pump_1", "Compressor_2"], "pressure": [5.6, 8.2]})
    buffer = io.BytesIO()
    df_orig.to_excel(buffer, index=False, engine="openpyxl")
    excel_bytes = buffer.getvalue()

    result = converter.convert_and_store(excel_bytes, "assets.xlsx")
    assert result["row_count"] == 2
    df_read = pd.read_csv(result["converted_csv_path"])
    assert "pressure" in df_read.columns

def test_convert_unstructured_text(converter):
    text = b"Maintenance Report Phase 1\nMotor bearing inspected on site.\nGrease replenished."
    result = converter.convert_and_store(text, "notes.txt")

    assert result["row_count"] == 3
    df = pd.read_csv(result["converted_csv_path"])
    assert "content" in df.columns

def test_convert_unknown_binary(converter):
    # Pure arbitrary binary payload (e.g. firmware or custom sensor blob)
    binary_bytes = bytes([0x00, 0xFF, 0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC] * 16)
    result = converter.convert_and_store(binary_bytes, "firmware.bin")

    assert result["status"] == "completed"
    assert result["row_count"] > 0
    assert os.path.exists(result["converted_csv_path"])

def test_list_and_stats(converter):
    converter.convert_and_store(b'{"key": "val1"}', "one.json")
    converter.convert_and_store(b'{"key": "val2"}', "two.json")

    files = converter.list_converted_files()
    assert len(files) == 2

    stats = converter.get_ingestion_stats()
    assert stats["total_files"] == 2
    assert stats["total_rows"] == 2
