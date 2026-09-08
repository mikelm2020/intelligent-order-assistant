import pytest

from app.services.document_ingestion import DocumentIngestionService


def test_split_text_creates_chunks_with_overlap():
    service = DocumentIngestionService(
        chunk_size=10,
        chunk_overlap=2,
    )

    chunks = service.split_text("abcdefghijklmnopqrst")

    assert chunks == [
        "abcdefghij",
        "ijklmnopqr",
        "qrst",
    ]


def test_split_text_returns_empty_list_for_empty_text():
    service = DocumentIngestionService()

    assert service.split_text("") == []


def test_chunk_overlap_must_be_smaller_than_chunk_size():
    with pytest.raises(
        ValueError,
        match="chunk_overlap must be smaller than chunk_size",
    ):
        DocumentIngestionService(
            chunk_size=100,
            chunk_overlap=100,
        )
