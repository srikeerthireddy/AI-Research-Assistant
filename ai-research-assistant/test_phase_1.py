"""
Test script for Phase 1 - Document Upload System
Run this to verify everything is working
"""
import requests
import json
import time
from pathlib import Path

API_URL = "http://localhost:8000"

def test_health_check():
    """Test API is running"""
    print("\n🔍 Test 1: Health Check")
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        if response.status_code == 200:
            print("✅ API is running!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API at http://localhost:8000")
        print("   Make sure backend is running: python -m app.main")
        return False

def test_upload_document():
    """Test document upload"""
    print("\n🔍 Test 2: Document Upload")
    
    # Create a test file
    test_file_path = Path("test_document.txt")
    test_file_path.write_text("This is a test document for Phase 1 testing.")
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': (test_file_path.name, f)}
            response = requests.post(
                f"{API_URL}/api/documents/upload",
                files=files,
                timeout=10
            )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Document uploaded successfully!")
            print(f"Document ID: {result.get('document_id')}")
            print(f"File size: {result.get('size')} bytes")
            return result.get('document_id')
        else:
            print(f"❌ Upload failed: {response.text}")
            return None
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None
    
    finally:
        # Cleanup
        test_file_path.unlink()

def test_list_documents():
    """Test listing documents"""
    print("\n🔍 Test 3: List Documents")
    
    try:
        response = requests.get(f"{API_URL}/api/documents", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            count = result.get('count', 0)
            print(f"✅ Found {count} documents")
            
            if count > 0:
                docs = result.get('documents', [])
                for doc in docs[:3]:  # Show first 3
                    print(f"  - {doc['original_filename']} (ID: {doc['document_id'][:8]}...)")
            
            return count > 0
        else:
            print(f"❌ Failed to list documents: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_get_document(document_id):
    """Test getting document details"""
    print(f"\n🔍 Test 4: Get Document Details")
    
    try:
        response = requests.get(
            f"{API_URL}/api/documents/{document_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            doc = result.get('document')
            print("✅ Document retrieved successfully!")
            print(f"File: {doc['original_filename']}")
            print(f"Size: {doc['file_size']} bytes")
            print(f"Uploaded: {doc['upload_time']}")
            return True
        else:
            print(f"❌ Failed to get document: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_parse_document(document_id):
    """Test document parsing"""
    print(f"\n🔍 Test 5: Parse Document (Extract Text)")
    
    try:
        response = requests.post(
            f"{API_URL}/api/documents/{document_id}/parse",
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            data = result.get('data', {})
            full_text = data.get('full_text', '')
            total_chars = data.get('total_characters', 0)
            
            print("✅ Document parsed successfully!")
            print(f"Total characters: {total_chars}")
            print(f"Text preview: {full_text[:100]}...")
            return True
        else:
            print(f"❌ Failed to parse document: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_delete_document(document_id):
    """Test document deletion"""
    print(f"\n🔍 Test 6: Delete Document")
    
    try:
        response = requests.delete(
            f"{API_URL}/api/documents/{document_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Document deleted successfully!")
            return True
        else:
            print(f"❌ Failed to delete document: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Phase 1 - Document Upload System Tests")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 6
    
    # Test 1: Health check
    if test_health_check():
        tests_passed += 1
    else:
        print("⚠️  Stopping tests - API not running")
        return
    
    # Test 2: Upload
    doc_id = test_upload_document()
    if doc_id:
        tests_passed += 1
    else:
        print("⚠️  Cannot continue without uploaded document")
        return
    
    # Test 3: List
    if test_list_documents():
        tests_passed += 1
    
    # Test 4: Get
    if test_get_document(doc_id):
        tests_passed += 1
    
    # Test 5: Parse
    if test_parse_document(doc_id):
        tests_passed += 1
    
    # Test 6: Delete
    if test_delete_document(doc_id):
        tests_passed += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"✅ Tests Passed: {tests_passed}/{tests_total}")
    print("=" * 60)
    
    if tests_passed == tests_total:
        print("\n🎉 All tests passed! Phase 1 is working perfectly!")
        print("\nNext steps:")
        print("1. Visit http://localhost:8501 to use the Streamlit frontend")
        print("2. Upload and manage documents through the UI")
        print("3. Proceed to Phase 2: PDF Parsing")
    else:
        print(f"\n⚠️  {tests_total - tests_passed} tests failed. Check errors above.")

if __name__ == "__main__":
    print("\n🚀 Starting Phase 1 tests...")
    print("Make sure both backend and frontend are running:\n")
    print("Backend: python -m app.main")
    print("Frontend: streamlit run frontend/app.py\n")
    
    time.sleep(2)
    run_all_tests()
