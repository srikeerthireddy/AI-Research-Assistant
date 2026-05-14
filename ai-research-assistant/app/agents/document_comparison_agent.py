"""
Document Comparison Agent
Enables semantic comparison across multiple documents
Uses LangGraph for orchestration (optional)
"""
try:
    from langgraph.graph import StateGraph, END
    HAS_LANGGRAPH = True
except Exception:
    StateGraph = None
    END = None
    HAS_LANGGRAPH = False
from typing import TypedDict, List, Dict, Any, Optional
from app.services.retriever import Retriever
from app.services.generator import Generator
import logging

logger = logging.getLogger(__name__)

class ComparisonState(TypedDict):
    """State for document comparison workflow"""
    document_ids: List[str]
    query: str
    retrieved_data: Dict[str, List[Dict]]
    comparison_analysis: str
    similarities: List[str]
    differences: List[str]
    status: str

class DocumentComparator:
    """Compare multiple documents using semantic analysis"""
    
    def __init__(self):
        self.retriever = Retriever()
        self.generator = Generator()
    
    def retrieve_from_documents(self, document_ids: List[str], query: str, top_k: int = 5) -> Dict[str, List[Dict]]:
        """Retrieve relevant chunks from each document"""
        results = {}
        
        for doc_id in document_ids:
            try:
                chunks = self.retriever.retrieve(
                    query=query,
                    document_id=doc_id,
                    top_k=top_k
                )
                results[doc_id] = chunks
            except Exception as e:
                logger.error(f"Error retrieving from {doc_id}: {str(e)}")
                results[doc_id] = []
        
        return results
    
    def analyze_similarities(self, retrieved_data: Dict[str, List[Dict]]) -> List[str]:
        """Identify similarities between documents"""
        similarities = []
        
        try:
            doc_ids = list(retrieved_data.keys())
            if len(doc_ids) >= 2:
                # Extract texts
                texts = {doc_id: " ".join([chunk["text"] for chunk in chunks]) 
                        for doc_id, chunks in retrieved_data.items()}
                
                # Generate comparison prompt
                prompt = f"""
                Analyze these document excerpts and identify key similarities:
                
                {chr(10).join([f"Document {i+1}:\n{texts[doc_id][:500]}..." for i, doc_id in enumerate(doc_ids)])}
                
                Provide 3-5 key similarities. Be specific.
                """
                
                response = self.generator.generate(prompt, max_tokens=500)
                similarities = [line.strip() for line in response.split('\n') if line.strip() and line.startswith('-')]
        
        except Exception as e:
            logger.error(f"Error analyzing similarities: {str(e)}")
        
        return similarities
    
    def analyze_differences(self, retrieved_data: Dict[str, List[Dict]]) -> List[str]:
        """Identify differences between documents"""
        differences = []
        
        try:
            doc_ids = list(retrieved_data.keys())
            if len(doc_ids) >= 2:
                texts = {doc_id: " ".join([chunk["text"] for chunk in chunks]) 
                        for doc_id, chunks in retrieved_data.items()}
                
                prompt = f"""
                Analyze these document excerpts and identify key differences:
                
                {chr(10).join([f"Document {i+1}:\n{texts[doc_id][:500]}..." for i, doc_id in enumerate(doc_ids)])}
                
                Provide 3-5 key differences. Be specific.
                """
                
                response = self.generator.generate(prompt, max_tokens=500)
                differences = [line.strip() for line in response.split('\n') if line.strip() and line.startswith('-')]
        
        except Exception as e:
            logger.error(f"Error analyzing differences: {str(e)}")
        
        return differences
    
    def generate_comparison_report(self, retrieved_data: Dict[str, List[Dict]], 
                                  similarities: List[str], differences: List[str],
                                  query: str) -> str:
        """Generate a comprehensive comparison report"""
        
        try:
            doc_count = len(retrieved_data)
            
            report = f"""
            # Document Comparison Report
            
            **Query:** {query}
            **Documents Compared:** {doc_count}
            
            ## Similarities
            {chr(10).join([f"- {sim}" for sim in similarities])}
            
            ## Differences
            {chr(10).join([f"- {diff}" for diff in differences])}
            
            ## Detailed Analysis
            """
            
            # Add detailed analysis
            for doc_id, chunks in retrieved_data.items():
                if chunks:
                    report += f"\n\n### Document {doc_id[:8]}...\n"
                    report += chunks[0].get("text", "No content")[:300] + "..."
            
            return report
        
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return f"Error generating comparison report: {str(e)}"
    
    def compare(self, document_ids: List[str], query: str) -> Dict[str, Any]:
        """Execute complete document comparison workflow"""
        
        try:
            if len(document_ids) < 2:
                return {
                    "success": False,
                    "error": "At least 2 documents required for comparison"
                }
            
            # Retrieve relevant chunks from each document
            retrieved_data = self.retrieve_from_documents(document_ids, query)
            
            # Analyze similarities and differences
            similarities = self.analyze_similarities(retrieved_data)
            differences = self.analyze_differences(retrieved_data)
            
            # Generate comprehensive report
            comparison_report = self.generate_comparison_report(
                retrieved_data, similarities, differences, query
            )
            
            return {
                "success": True,
                "comparison": comparison_report,
                "similarities": similarities,
                "differences": differences,
                "documents_compared": len(document_ids),
                "query": query
            }
        
        except Exception as e:
            logger.error(f"Comparison error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
