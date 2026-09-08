"""Tests for the PDF -> chunk pipeline in injest.py. The embedding/Chroma
side of main() is intentionally not covered here — it's thin glue over
SentenceTransformer and chromadb, better exercised end to end than mocked
piece by piece."""

import pytest

import injest


# ---------------------------------------------------------------------------
# chunk_text
# ---------------------------------------------------------------------------

def test_chunk_text_returns_single_chunk_when_text_fits_in_one():
    assert injest.chunk_text("hello world", size=100, overlap=10) == ["hello world"]


def test_chunk_text_returns_empty_list_for_empty_text():
    assert injest.chunk_text("", size=100, overlap=10) == []


def test_chunk_text_splits_long_text_into_overlapping_chunks():
    text = "a" * 25
    chunks = injest.chunk_text(text, size=10, overlap=2)

    # windows start at 0, 8, 16, 24 (stride = size - overlap = 8); the last
    # two windows run past the end of the 25-char text and get truncated
    assert chunks == ["a" * 10, "a" * 10, "a" * 9, "a"]


def test_chunk_text_consecutive_chunks_overlap_by_requested_amount():
    text = "0123456789abcdefghij"  # 20 distinct chars, easy to eyeball overlap
    chunks = injest.chunk_text(text, size=8, overlap=3)

    for prev, nxt in zip(chunks, chunks[1:]):
        assert prev[-3:] == nxt[:3]


# ---------------------------------------------------------------------------
# parse_pdf
# ---------------------------------------------------------------------------

class FakePage:
    def __init__(self, text):
        self._text = text

    def get_text(self):
        return self._text


class FakeDoc:
    """Stands in for pymupdf's Document: iterable over pages, closable."""

    def __init__(self, page_texts):
        self._pages = [FakePage(t) for t in page_texts]
        self.closed = False

    def __iter__(self):
        return iter(self._pages)

    def close(self):
        self.closed = True


def test_parse_pdf_pairs_1_indexed_page_numbers_with_text(monkeypatch):
    fake_doc = FakeDoc(["first page", "second page"])
    monkeypatch.setattr(injest.pymupdf, "open", lambda path: fake_doc)

    assert injest.parse_pdf("irrelevant.pdf") == [(1, "first page"), (2, "second page")]


def test_parse_pdf_skips_blank_and_whitespace_only_pages(monkeypatch):
    fake_doc = FakeDoc(["text", "   \n\t  ", ""])
    monkeypatch.setattr(injest.pymupdf, "open", lambda path: fake_doc)

    pages = injest.parse_pdf("irrelevant.pdf")

    assert pages == [(1, "text")]


def test_parse_pdf_closes_the_document(monkeypatch):
    fake_doc = FakeDoc(["text"])
    monkeypatch.setattr(injest.pymupdf, "open", lambda path: fake_doc)

    injest.parse_pdf("irrelevant.pdf")

    assert fake_doc.closed is True


# ---------------------------------------------------------------------------
# build_records
# ---------------------------------------------------------------------------

def test_build_records_assembles_ids_docs_and_metas(monkeypatch, tmp_path):
    # parse_pdf is unit-tested above, so stub it here and drive build_records
    # purely off (pdf name -> pages) to keep this test about the assembly
    # logic, not PDF parsing.
    pages_by_pdf = {
        "a.pdf": [(1, "chunk-a1")],
        "b.pdf": [(1, "chunk-b1"), (2, "chunk-b2")],
    }
    monkeypatch.setattr(injest, "parse_pdf", lambda path: pages_by_pdf[path.name])
    monkeypatch.setattr(injest, "chunk_text", lambda text, size, overlap: [text])

    for name in pages_by_pdf:
        (tmp_path / name).write_bytes(b"")

    ids, docs, metas = injest.build_records(tmp_path)

    assert ids == ["a_p1_c0", "b_p1_c0", "b_p2_c0"]
    assert docs == ["chunk-a1", "chunk-b1", "chunk-b2"]
    assert metas == [
        {"source": "a.pdf", "page": 1, "chunk": 0},
        {"source": "b.pdf", "page": 1, "chunk": 0},
        {"source": "b.pdf", "page": 2, "chunk": 0},
    ]


def test_build_records_processes_pdfs_in_sorted_order(monkeypatch, tmp_path):
    monkeypatch.setattr(injest, "parse_pdf", lambda path: [(1, path.name)])
    monkeypatch.setattr(injest, "chunk_text", lambda text, size, overlap: [text])

    for name in ("z.pdf", "a.pdf", "m.pdf"):
        (tmp_path / name).write_bytes(b"")

    ids, docs, metas = injest.build_records(tmp_path)

    assert docs == ["a.pdf", "m.pdf", "z.pdf"]


def test_build_records_returns_empty_lists_when_directory_has_no_pdfs(tmp_path):
    ids, docs, metas = injest.build_records(tmp_path)

    assert (ids, docs, metas) == ([], [], [])


def test_build_records_ignores_non_pdf_files(monkeypatch, tmp_path):
    monkeypatch.setattr(injest, "parse_pdf", lambda path: [(1, path.name)])
    monkeypatch.setattr(injest, "chunk_text", lambda text, size, overlap: [text])

    (tmp_path / "notes.txt").write_bytes(b"")
    (tmp_path / "real.pdf").write_bytes(b"")

    ids, docs, metas = injest.build_records(tmp_path)

    assert docs == ["real.pdf"]
