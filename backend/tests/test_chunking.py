from app.rag.chunking import chunk_segments
from app.rag.loaders import Segment


def test_prose_respects_size_and_page_boundaries():
    segs = [Segment("alpha sentence. " * 80, {"page": 1}), Segment("beta sentence. " * 80, {"page": 2})]
    chunks = chunk_segments(segs, "pdf", chunk_size=300, chunk_overlap=50)
    assert len(chunks) > 2
    assert all(len(c.text) <= 300 for c in chunks)
    for c in chunks:  # no chunk mixes pages
        assert ("alpha" in c.text) == (c.metadata["page"] == 1)
        assert ("beta" in c.text) == (c.metadata["page"] == 2)


def test_overlap_repeats_content_between_neighbours():
    text = " ".join(f"word{i}" for i in range(200))
    chunks = chunk_segments([Segment(text, {})], "txt", chunk_size=200, chunk_overlap=60)
    first_tail = chunks[0].text.split()[-3:]
    assert any(w in chunks[1].text for w in first_tail)


def test_short_text_is_single_chunk():
    chunks = chunk_segments([Segment("tiny", {})], "txt", chunk_size=300, chunk_overlap=50)
    assert [c.text for c in chunks] == ["tiny"]


def test_csv_is_one_chunk_per_row_with_metadata():
    segs = [Segment("a: 1 | b: 2", {"row": 2}), Segment("a: 3 | b: 4", {"row": 3})]
    chunks = chunk_segments(segs, "csv", chunk_size=300, chunk_overlap=50)
    assert [c.metadata["row"] for c in chunks] == [2, 3]
    assert chunks[0].text == "a: 1 | b: 2"
