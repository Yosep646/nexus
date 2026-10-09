from backend.database import storage
from backend.reports.pdf import build_report


def test_pdf_report(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "report.db")
    storage.init_db()
    camera = storage.add_camera("Huanuco", "http://192.168.1.10:8080/video")
    storage.save_detection(camera["id"], "huayco", 0.94, "pending_human_review")
    pdf = build_report()
    assert pdf.startswith(b"%PDF")
    assert len(pdf) > 1000
    assert b"192.168.1.10" not in pdf
