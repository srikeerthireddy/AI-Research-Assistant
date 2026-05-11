"""
Test Suite for Phase 2: PDF Parsing & Text Analysis
Tests advanced extraction, text processing, and analysis features
"""
import pytest
import requests
import json
from pathlib import Path
import time

# API Configuration
API_BASE_URL = "http://localhost:8000"
TIMEOUT = 30

# Test data
TEST_PDF_PATH = Path(__file__).parent / "test_data" / "sample.pdf"
TEST_TXT_PATH = Path(__file__).parent / "test_data" / "sample.txt"

# Sample text for testing
SAMPLE_TEXT = """
Introduction
This is a test document for Phase 2 testing.
It contains multiple sections and paragraphs.

Section 1: Overview
The system processes documents with advanced extraction methods.
It detects structure and generates summaries automatically.

Section 2: Features
- Text extraction
- Structure detection
- Quality assessment
- Automatic summarization

Conclusion
Phase 2 provides robust text processing capabilities.
The system is ready for production use.
"""


class TestPhase2TextAnalysis:
    """Test text analysis functionality"""
    
    @pytest.fixture
    def uploaded_document(self):
        """Upload a test document and return its ID"""
        files = {"file": ("test_document.txt", SAMPLE_TEXT.encode())}
        response = requests.post(
            f"{API_BASE_URL}/api/documents/upload",
            files=files,
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        document_id = response.json()["document_id"]
        yield document_id
        
        # Cleanup
        requests.delete(f"{API_BASE_URL}/api/documents/{document_id}", timeout=TIMEOUT)
    
    def test_text_analysis_endpoint(self, uploaded_document):
        """Test /api/documents/{id}/analyze endpoint"""
        response = requests.post(
            f"{API_BASE_URL}/api/documents/{uploaded_document}/analyze",
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["success"] is True
        assert data["document_id"] == uploaded_document
        assert "analysis" in data
        
        analysis = data["analysis"]
        assert "processed_text" in analysis
        assert "sections" in analysis
        assert "summary" in analysis
        assert "statistics" in analysis
        assert "language_info" in analysis
    
    def test_text_statistics(self, uploaded_document):
        """Test text statistics calculation"""
        response = requests.post(
            f"{API_BASE_URL}/api/documents/{uploaded_document}/analyze",
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        stats = response.json()["analysis"]["statistics"]
        
        # Verify statistics fields
        assert stats["characters"] > 0
        assert stats["words"] > 0
        assert stats["sentences"] > 0
        assert stats["paragraphs"] > 0
        assert stats["avg_word_length"] > 0
        assert stats["avg_sentence_length"] > 0
        assert stats["unique_words"] > 0
    
    def test_section_extraction(self, uploaded_document):
        """Test section extraction"""
        response = requests.post(
            f"{API_BASE_URL}/api/documents/{uploaded_document}/analyze",
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        sections = response.json()["analysis"]["sections"]
        
        # Verify sections
        assert len(sections) > 0
        
        for section in sections:
            assert "id" in section
            assert "text" in section
            assert "length" in section
            assert "word_count" in section
            assert len(section["text"]) > 0
    
    def test_language_detection(self, uploaded_document):
        """Test language information detection"""
        response = requests.post(
            f"{API_BASE_URL}/api/documents/{uploaded_document}/analyze",
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        lang_info = response.json()["analysis"]["language_info"]
        
        # Verify language info fields
        assert "has_numbers" in lang_info
        assert "has_urls" in lang_info
        assert "has_emails" in lang_info
        assert "code_likelihood" in lang_info
        assert 0 <= lang_info["code_likelihood"] <= 1


class TestPhase2TextChunking:
    """Test text chunking functionality"""
    
    @pytest.fixture
    def uploaded_document(self):
        """Upload a test document and return its ID"""
        files = {"file": ("test_document.txt", SAMPLE_TEXT.encode())}
        response = requests.post(
            f"{API_BASE_URL}/api/documents/upload",
            files=files,
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        document_id = response.json()["document_id"]
        yield document_id
        
        # Cleanup
        requests.delete(f"{API_BASE_URL}/api/documents/{document_id}", timeout=TIMEOUT)
    
    def test_chunks_endpoint(self, uploaded_document):
        """Test /api/documents/{id}/chunks endpoint"""
        response = requests.post(
            f"{API_BASE_URL}/api/documents/{uploaded_document}/chunks",
            params={"chunk_size": 500, "overlap": 100},
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["success"] is True
        assert data["document_id"] == uploaded_document
        assert data["chunk_size"] == 500
        assert data["overlap"] == 100
        assert "chunks" in data
        assert isinstance(data["chunks"], list)
    
    def test_chunk_structure(self, uploaded_document):
        """Test chunk data structure"""
        response = requests.post(
            f"{API_BASE_URL}/api/documents/{uploaded_document}/chunks",
            params={"chunk_size": 500, "overlap": 100},
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        chunks = response.json()["chunks"]
        
        assert len(chunks) > 0
        
        for chunk in chunks:
            assert "chunk_id" in chunk
            assert "text" in chunk
            assert "start_char" in chunk
            assert "end_char" in chunk
            assert "length" in chunk
            assert "word_count" in chunk
            assert chunk["length"] == len(chunk["text"])
    
    def test_chunk_overlap(self, uploaded_document):
        """Test that chunks have correct overlap"""
        chunk_size = 1000
        overlap = 200
        
        response = requests.post(
            f"{API_BASE_URL}/api/documents/{uploaded_document}/chunks",
            params={"chunk_size": chunk_size, "overlap": overlap},
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        chunks = response.json()["chunks"]
        
        if len(chunks) > 1:
            # Check overlap between consecutive chunks
            for i in range(len(chunks) - 1):
                current_end = chunks[i]["end_char"]
                next_start = chunks[i + 1]["start_char"]
                
                # The difference should be approximately chunk_size - overlap
                actual_step = next_start - chunks[i]["start_char"]
                expected_step = chunk_size - overlap
                
                # Allow some tolerance
                assert abs(actual_step - expected_step) <= overlap


class TestPhase2Summarization:
    """Test document summarization"""
    
    @pytest.fixture
    def uploaded_document(self):
        """Upload a test document and return its ID"""
        files = {"file": ("test_document.txt", SAMPLE_TEXT.encode())}
        response = requests.post(
            f"{API_BASE_URL}/api/documents/upload",
            files=files,
            timeout=TIMEOUT
        )
        assert response.status_code == 200
        document_id = response.json()["document_id"]
        yield document_id
        
        # Cleanup
        requests.delete(f"{API_BASE_URL}/api/documents/{document_id}", timeout=TIMEOUT)
    
    def test_summary_endpoint(self, uploaded_document):
        """Test /api/documents/{id}/summary endpoint"""
        response = requests.get(
            f"{API_BASE_URL}/api/documents/{uploaded_document}/summary",
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["success"] is True
        assert data["document_id"] == uploaded_document
        assert "summary" in data
        assert "statistics" in data
        assert "section_count" in data
    
    def test_summary_content(self, uploaded_document):
        """Test that summary is generated correctly"""
        response = requests.get(
            f"{API_BASE_URL}/api/documents/{uploaded_document}/summary",
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        summary = data["summary"]
        
        # Summary should not be empty
        assert len(summary) > 0
        
        # Summary should be shorter than original
        stats = data["statistics"]
        assert len(summary) < stats.get("characters", float('inf'))
    
    def test_summary_statistics(self, uploaded_document):
        """Test summary statistics"""
        response = requests.get(
            f"{API_BASE_URL}/api/documents/{uploaded_document}/summary",
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        stats = data["statistics"]
        
        # Verify statistics
        assert stats["words"] > 0
        assert stats["sentences"] > 0
        assert data["section_count"] >= 0


class TestPhase2ErrorHandling:
    """Test error handling in Phase 2"""
    
    def test_analyze_nonexistent_document(self):
        """Test analyzing a document that doesn't exist"""
        response = requests.post(
            f"{API_BASE_URL}/api/documents/nonexistent/analyze",
            timeout=TIMEOUT
        )
        
        assert response.status_code == 404
    
    def test_chunks_nonexistent_document(self):
        """Test chunking a document that doesn't exist"""
        response = requests.post(
            f"{API_BASE_URL}/api/documents/nonexistent/chunks",
            timeout=TIMEOUT
        )
        
        assert response.status_code == 404
    
    def test_summary_nonexistent_document(self):
        """Test summarizing a document that doesn't exist"""
        response = requests.get(
            f"{API_BASE_URL}/api/documents/nonexistent/summary",
            timeout=TIMEOUT
        )
        
        assert response.status_code == 404


class TestPhase2Integration:
    """Integration tests for complete Phase 2 workflow"""
    
    def test_complete_workflow(self):
        """Test complete Phase 2 workflow"""
        # Step 1: Upload document
        files = {"file": ("test_document.txt", SAMPLE_TEXT.encode())}
        upload_response = requests.post(
            f"{API_BASE_URL}/api/documents/upload",
            files=files,
            timeout=TIMEOUT
        )
        
        assert upload_response.status_code == 200
        document_id = upload_response.json()["document_id"]
        
        try:
            # Step 2: Analyze text
            analyze_response = requests.post(
                f"{API_BASE_URL}/api/documents/{document_id}/analyze",
                timeout=TIMEOUT
            )
            assert analyze_response.status_code == 200
            assert analyze_response.json()["success"] is True
            
            # Step 3: Create chunks
            chunks_response = requests.post(
                f"{API_BASE_URL}/api/documents/{document_id}/chunks",
                params={"chunk_size": 500, "overlap": 100},
                timeout=TIMEOUT
            )
            assert chunks_response.status_code == 200
            assert chunks_response.json()["success"] is True
            assert len(chunks_response.json()["chunks"]) > 0
            
            # Step 4: Generate summary
            summary_response = requests.get(
                f"{API_BASE_URL}/api/documents/{document_id}/summary",
                timeout=TIMEOUT
            )
            assert summary_response.status_code == 200
            assert summary_response.json()["success"] is True
            assert len(summary_response.json()["summary"]) > 0
        
        finally:
            # Cleanup
            requests.delete(f"{API_BASE_URL}/api/documents/{document_id}", timeout=TIMEOUT)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])
