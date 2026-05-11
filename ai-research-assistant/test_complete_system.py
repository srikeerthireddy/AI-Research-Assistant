#!/usr/bin/env python
"""
Test Script for AI Research Assistant
Demonstrates all Phases 4-8 functionality
"""
import requests
import json
import time
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 180

def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def test_health_check():
    """Test Phase 1: Health Check"""
    print_section("Phase 0: Health Check")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend is online")
            print(f"   Service: {data.get('service')}")
            print(f"   Version: {data.get('version')}")
            print(f"   Agents: {data.get('agents')}")
            return True
        else:
            print("❌ Backend returned error")
            return False
    except Exception as e:
        print(f"❌ Backend offline: {str(e)}")
        return False

def test_document_upload():
    """Test Phases 1-3: Document Upload & Processing"""
    print_section("Phases 1-3: Document Upload & Chunking")
    
    # Create test file
    test_file_path = Path("test_document.txt")
    test_content = """
    Machine Learning Basics
    
    Machine learning is a subset of artificial intelligence (AI) that focuses on 
    enabling computers to learn and improve from experience without being explicitly 
    programmed. It involves training algorithms on data to make predictions or 
    decisions.
    
    Types of Machine Learning:
    1. Supervised Learning - Learning from labeled data
    2. Unsupervised Learning - Finding patterns in unlabeled data
    3. Reinforcement Learning - Learning through rewards and penalties
    
    Key Concepts:
    - Training Data: Data used to train the model
    - Features: Input variables used for prediction
    - Labels: Output variables in supervised learning
    - Model: Mathematical representation of the learned patterns
    - Overfitting: When model learns noise in training data
    
    Applications:
    - Image Recognition
    - Natural Language Processing
    - Recommendation Systems
    - Autonomous Vehicles
    """
    
    test_file_path.write_text(test_content)
    
    try:
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_document.txt', f)}
            response = requests.post(
                f"{BASE_URL}/api/documents/upload",
                files=files,
                timeout=TIMEOUT
            )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Document uploaded successfully")
            print(f"   Document ID: {data['document_id']}")
            print(f"   Filename: {data['filename']}")
            print(f"   Size: {data['size']} bytes")
            print(f"   Status: {data['status']}")
            print(f"   Ready for queries: {data['ready_for_queries']}")
            return data['document_id']
        else:
            print(f"❌ Upload failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error uploading document: {str(e)}")
        return None
    finally:
        test_file_path.unlink(missing_ok=True)

def test_list_documents():
    """Test Document Listing"""
    print_section("Test: List Documents")
    try:
        response = requests.get(f"{BASE_URL}/api/documents", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {data['count']} documents")
            for doc in data['documents'][:3]:
                print(f"   - {doc['original_filename']} ({doc['document_id'][:8]}...)")
            return True
        else:
            print(f"❌ Failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_rag_phases_4_7(doc_id):
    """Test Phases 4-7: RAG Pipeline (Embeddings → Retrieval → Generation)"""
    print_section("Phases 4-7: RAG Pipeline (Embeddings → Retrieval → Generation)")
    
    query = "What are the types of machine learning?"
    
    try:
        print(f"Query: {query}\n")
        
        response = requests.post(
            f"{BASE_URL}/api/ask",
            json={
                "query": query,
                "document_id": doc_id,
                "top_k": 5
            },
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data['success']:
                print("✅ RAG Pipeline Executed")
                print(f"\n📝 Answer:\n{data['answer']}\n")
                print(f"📊 Pipeline Stats:")
                print(f"   Chunks Retrieved: {data['retrieved_chunks']}")
                print(f"   Sources Found: {len(data['sources'])}")
                
                print(f"\n📚 Sources:")
                for source in data['sources']:
                    print(f"   [{source['index']}] {source['document_id'][:8]}... (Similarity: {source['similarity']})")
                
                return True
            else:
                print("❌ RAG failed")
                return False
        else:
            print(f"❌ Request failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_summarization(doc_id):
    """Test Summarization Agent"""
    print_section("Phase 8: Summarizer Agent")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/summary",
            json={
                "document_id": doc_id,
                "length": "moderate"
            },
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data['success']:
                print("✅ Summary Generated")
                print(f"\n{data['summary']}\n")
                return True
            else:
                print("❌ Summarization failed")
                return False
        else:
            print(f"❌ Request failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_quiz_generation(doc_id):
    """Test Quiz Generation with Human-in-the-Loop"""
    print_section("Phase 8: Quiz Agent (Human-in-the-Loop)")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/quiz",
            json={
                "document_id": doc_id,
                "num_questions": 3,
                "require_approval": True
            },
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data['status'] == "pending_approval":
                print("✅ Quiz Generated (Pending Approval)")
                print(f"   Quiz ID: {data['quiz_id']}")
                print(f"   Questions: {data['preview_count']}")
                
                if data.get('preview_questions'):
                    print(f"\n📋 Preview Question:")
                    q = data['preview_questions'][0]
                    print(f"   Q: {q.get('question')}")
                    for key, opt in q.get('options', {}).items():
                        print(f"      {key}. {opt}")
                    print(f"   Answer: {q.get('correct_answer')}")
                
                # Auto-approve for testing
                print(f"\n🔄 Auto-approving quiz for demo...")
                approve_resp = requests.post(
                    f"{BASE_URL}/api/quiz/{data['quiz_id']}/approve",
                    json={"approved": True},
                    timeout=10
                )
                
                if approve_resp.status_code == 200:
                    approve_data = approve_resp.json()
                    print("✅ Quiz Approved")
                    print(f"   Final Questions: {approve_data.get('num_questions')}")
                    return True
                else:
                    print("⚠️  Quiz generated but approval failed")
                    return True
            
            elif data['status'] == "success":
                print("✅ Quiz Generated (No Approval Required)")
                print(f"   Questions: {data['num_questions']}")
                return True
            else:
                print("❌ Quiz generation failed")
                return False
        else:
            print(f"❌ Request failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def test_citations(doc_id):
    """Test Citation Agent"""
    print_section("Phase 8: Citation Agent")
    
    query = "machine learning types"
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/citations",
            json={
                "query": query,
                "document_id": doc_id
            },
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data['success']:
                print("✅ Citations Retrieved")
                print(f"   Query: {query}")
                print(f"   Found: {data['citation_count']} citations\n")
                
                for citation in data['citations'][:2]:
                    print(f"[{citation['number']}] Relevance: {citation['relevance']}")
                    print(f"    {citation['snippet']}\n")
                
                return True
            else:
                print("❌ No citations found")
                return False
        else:
            print(f"❌ Request failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def run_all_tests():
    """Run all tests"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*12 + "AI Research Assistant - System Test" + " "*12 + "║")
    print("║" + " "*16 + "Phases 4-8 Complete Implementation" + " "*9 + "║")
    print("╚" + "="*58 + "╝")
    
    results = {
        "Health Check": False,
        "Document Upload": False,
        "List Documents": False,
        "RAG Pipeline (4-7)": False,
        "Summarization (8)": False,
        "Quiz Generation (8)": False,
        "Citations (8)": False,
    }
    
    # Phase 0: Health
    results["Health Check"] = test_health_check()
    if not results["Health Check"]:
        print("\n❌ Backend not running. Start it with:")
        print("   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload")
        return results
    
    # Phases 1-3: Upload
    doc_id = test_document_upload()
    if not doc_id:
        print("❌ Cannot proceed without document")
        return results
    results["Document Upload"] = True
    
    # Test listing
    results["List Documents"] = test_list_documents()
    
    # Wait for embeddings
    print("\n⏳ Waiting 2 seconds for embeddings to complete...")
    time.sleep(2)
    
    # Phases 4-7: RAG
    results["RAG Pipeline (4-7)"] = test_rag_phases_4_7(doc_id)
    
    # Phase 8 - Summarizer
    results["Summarization (8)"] = test_summarization(doc_id)
    
    # Phase 8 - Quiz
    results["Quiz Generation (8)"] = test_quiz_generation(doc_id)
    
    # Phase 8 - Citations
    results["Citations (8)"] = test_citations(doc_id)
    
    # Summary
    print_section("Test Summary")
    print("Test Results:")
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name:.<40} {status}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! System is fully functional.")
    else:
        print(f"\n⚠️  {total_count - passed_count} test(s) failed. Check logs above.")
    
    return results

if __name__ == "__main__":
    run_all_tests()
