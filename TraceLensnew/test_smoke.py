import io
from PIL import Image
from forensic_engine import analyze_uploaded_file
from report_generator import build_json_report, build_html_report, build_pdf_report

def test_image_pipeline():
    b = io.BytesIO()
    Image.new("RGB", (24, 16), (120, 80, 40)).save(b, format="JPEG")
    result = analyze_uploaded_file(b.getvalue(), "test.jpg")
    assert result["media_type"] == "image"
    assert len(result["file_facts"]["sha256"]) == 64
    assert "width" in result["metadata"]
    assert build_json_report(result)
    assert b"TraceLens" in build_html_report(result)
    assert build_pdf_report(result).startswith(b"%PDF")
