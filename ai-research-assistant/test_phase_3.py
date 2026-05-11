"""
Test Suite for Phase 3: Intelligent Chunking
"""

import pytest
import requests

API_BASE_URL = "http://localhost:8000"
TIMEOUT = 30

SAMPLE_TEXT = """
Introduction
This phase introduces intelligent chunking for RAG pipelines.
It preserves heading boundaries and semantic continuity.

System Goals
The chunker should avoid splitting critical meaning across boundaries.
Each chunk should include enough context for retrieval.

Implementation Details
We use paragraph-first segmentation and optional heading awareness.
We attach metadata such as keywords and neighbor links.

Evaluation
Chunk quality improves when context overlap is preserved.
Heading-sensitive splitting helps maintain topical coherence.
"""


@pytest.fixture
def uploaded_document():
    files = {"file": ("phase3_doc.txt", SAMPLE_TEXT.encode())}
    response = requests.post(f"{API_BASE_URL}/api/documents/upload", files=files, timeout=TIMEOUT)
    assert response.status_code == 200
    document_id = response.json()["document_id"]
    yield document_id
    requests.delete(f"{API_BASE_URL}/api/documents/{document_id}", timeout=TIMEOUT)


def test_intelligent_chunks_endpoint_success(uploaded_document):
    response = requests.post(
        f"{API_BASE_URL}/api/documents/{uploaded_document}/chunks/intelligent",
        params={
            "target_chunk_size": 700,
            "min_chunk_size": 250,
            "overlap": 120,
            "respect_headers": True,
        },
        timeout=TIMEOUT,
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["document_id"] == uploaded_document
    assert data["strategy"] == "semantic_v1"
    assert "metadata" in data
    assert "chunks" in data
    assert isinstance(data["chunks"], list)
    assert len(data["chunks"]) > 0


def test_intelligent_chunk_fields(uploaded_document):
    response = requests.post(
        f"{API_BASE_URL}/api/documents/{uploaded_document}/chunks/intelligent",
        params={"target_chunk_size": 700, "min_chunk_size": 250, "overlap": 120},
        timeout=TIMEOUT,
    )
    assert response.status_code == 200

    chunks = response.json()["chunks"]
    first = chunks[0]

    required_fields = [
        "chunk_id",
        "text",
        "start_char",
        "end_char",
        "length",
        "word_count",
        "section_title",
        "heading_count",
        "block_count",
        "keywords",
        "prev_chunk_id",
        "next_chunk_id",
        "topic_signature",
    ]

    for field in required_fields:
        assert field in first


def test_intelligent_chunk_relationships(uploaded_document):
    response = requests.post(
        f"{API_BASE_URL}/api/documents/{uploaded_document}/chunks/intelligent",
        params={"target_chunk_size": 450, "min_chunk_size": 200, "overlap": 80},
        timeout=TIMEOUT,
    )
    assert response.status_code == 200

    chunks = response.json()["chunks"]
    assert len(chunks) >= 1

    for i, chunk in enumerate(chunks):
        expected_prev = i - 1 if i > 0 else None
        expected_next = i + 1 if i < len(chunks) - 1 else None

        assert chunk["prev_chunk_id"] == expected_prev
        assert chunk["next_chunk_id"] == expected_next


def test_intelligent_chunk_metadata_values(uploaded_document):
    response = requests.post(
        f"{API_BASE_URL}/api/documents/{uploaded_document}/chunks/intelligent",
        params={
            "target_chunk_size": 900,
            "min_chunk_size": 300,
            "overlap": 100,
            "respect_headers": True,
        },
        timeout=TIMEOUT,
    )
    assert response.status_code == 200

    metadata = response.json()["metadata"]

    assert metadata["target_chunk_size"] == 900
    assert metadata["min_chunk_size"] == 300
    assert metadata["overlap"] == 100
    assert metadata["respect_headers"] is True
    assert metadata["total_blocks"] >= 1
    assert metadata["total_chunks"] >= 1


def test_intelligent_chunks_nonexistent_document():
    response = requests.post(
        f"{API_BASE_URL}/api/documents/nonexistent/chunks/intelligent",
        timeout=TIMEOUT,
    )
    assert response.status_code == 404


def test_intelligent_chunks_header_mode_toggle(uploaded_document):
    with_headers = requests.post(
        f"{API_BASE_URL}/api/documents/{uploaded_document}/chunks/intelligent",
        params={"target_chunk_size": 700, "respect_headers": True},
        timeout=TIMEOUT,
    )
    without_headers = requests.post(
        f"{API_BASE_URL}/api/documents/{uploaded_document}/chunks/intelligent",
        params={"target_chunk_size": 700, "respect_headers": False},
        timeout=TIMEOUT,
    )

    assert with_headers.status_code == 200
    assert without_headers.status_code == 200

    a = with_headers.json()
    b = without_headers.json()

    assert a["metadata"]["respect_headers"] is True
    assert b["metadata"]["respect_headers"] is False
