import pytest
from reportlab.pdfgen import canvas

from app.rag.loaders import load_csv, load_pdf, load_txt
from app.utils.errors import DocumentProcessingError, InvalidFileError


def make_pdf(path, pages):
    c = canvas.Canvas(str(path))
    for text in pages:
        c.drawString(72, 720, text)
        c.showPage()
    c.save()


def test_pdf_preserves_page_numbers(tmp_path):
    p = tmp_path / "a.pdf"
    make_pdf(p, ["Revenue was 15 million", "Costs were 9 million"])
    segs = load_pdf(p)
    assert [s.metadata["page"] for s in segs] == [1, 2]
    assert "Revenue" in segs[0].text


def test_pdf_without_text_is_rejected(tmp_path):
    p = tmp_path / "blank.pdf"
    make_pdf(p, [""])
    with pytest.raises(DocumentProcessingError):
        load_pdf(p)


def test_corrupt_pdf_is_rejected(tmp_path):
    p = tmp_path / "bad.pdf"
    p.write_bytes(b"%PDF-1.4 this is not really a pdf")
    with pytest.raises(InvalidFileError):
        load_pdf(p)


def test_txt_reads_utf8_and_latin1(tmp_path):
    (tmp_path / "u.txt").write_text("héllo world", encoding="utf-8")
    (tmp_path / "l.txt").write_bytes("café".encode("latin-1"))
    assert load_txt(tmp_path / "u.txt")[0].text == "héllo world"
    assert load_txt(tmp_path / "l.txt")[0].text == "café"


def test_blank_txt_is_rejected(tmp_path):
    p = tmp_path / "e.txt"
    p.write_text("   \n  ")
    with pytest.raises(DocumentProcessingError):
        load_txt(p)


def test_csv_rows_keep_column_names_and_row_numbers(tmp_path):
    p = tmp_path / "sales.csv"
    p.write_text("region,revenue\nEMEA,100\nAPAC,250\n")
    segs = load_csv(p)
    assert segs[0].text == "region: EMEA | revenue: 100"
    assert [s.metadata["row"] for s in segs] == [2, 3]  # header is row 1


def test_csv_skips_empty_cells_and_rejects_header_only(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("a,b\n1,\n")
    assert load_csv(p)[0].text == "a: 1"
    h = tmp_path / "h.csv"
    h.write_text("a,b\n")
    with pytest.raises(DocumentProcessingError):
        load_csv(h)


def test_csv_row_limit(tmp_path):
    p = tmp_path / "big.csv"
    p.write_text("a\n" + "\n".join(str(i) for i in range(20)))
    with pytest.raises(DocumentProcessingError):
        load_csv(p, max_rows=10)
