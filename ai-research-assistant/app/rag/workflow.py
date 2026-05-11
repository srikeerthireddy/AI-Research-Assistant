"""
RAG Workflow - Orchestrates the Retrieval-Augmented Generation pipeline with LangGraph.
Phase 8: Multi-Agent System with LangGraph orchestration
"""
import logging
from typing import Dict, List, Any, Optional
import json

from langgraph.graph import StateGraph, END
from app.agents.research_agent import ResearchAgent
from app.agents.summarizer_agent import SummarizerAgent
from app.agents.quiz_agent import QuizAgent
from app.agents.citation_agent import CitationAgent
from app.services.embeddings import EmbeddingsService
from app.services.retriever import RetrieverService
from app.services.generator import GeneratorService
from app.database.chroma_db import ChromaVectorDB

logger = logging.getLogger(__name__)


class RAGState:
    """State object for RAG workflow"""
    def __init__(self):
        self.query: str = ""
        self.document_id: Optional[str] = None
        self.action: str = "answer"  # answer, summarize, quiz, cite
        self.result: Dict = {}
        self.context: str = ""
        self.sources: List[Dict] = []


class RAGWorkflow:
    """
    Orchestrates the complete RAG pipeline using LangGraph
    
    Flow:
    1. Parse request
    2. Route to appropriate agent
    3. Retrieve relevant context
    4. Generate response
    5. Format output with citations
    """
    
    def __init__(self):
        """Initialize RAG workflow with all agents"""
        logger.info("Initializing RAG Workflow")
        
        # Initialize agents
        self.research_agent = ResearchAgent()
        self.summarizer_agent = SummarizerAgent()
        self.quiz_agent = QuizAgent()
        self.citation_agent = CitationAgent()
        
        # Initialize services
        self.embeddings = EmbeddingsService()
        self.retriever = RetrieverService()
        self.generator = GeneratorService()
        self.vector_db = ChromaVectorDB()
        
        # Build workflow graph
        self.graph = self._build_workflow_graph()
        
        logger.info("✅ RAG Workflow initialized")
    
    def _build_workflow_graph(self):
        """Build LangGraph workflow"""
        workflow = StateGraph(dict)
        
        # Define nodes
        workflow.add_node("parse_request", self._parse_request)
        workflow.add_node("research", self._research_node)
        workflow.add_node("summarize", self._summarize_node)
        workflow.add_node("quiz", self._quiz_node)
        workflow.add_node("citations", self._citations_node)
        workflow.add_node("format_output", self._format_output)
        
        # Define edges with routing
        workflow.add_edge("parse_request", "format_output")  # Route after parsing
        workflow.add_edge("research", "citations")
        workflow.add_edge("summarize", "citations")
        workflow.add_edge("quiz", "format_output")
        workflow.add_edge("citations", "format_output")
        workflow.add_edge("format_output", END)
        
        # Set entry point
        workflow.set_entry_point("parse_request")
        
        return workflow.compile()
    
    def _parse_request(self, state: Dict) -> Dict:
        """Parse incoming request and route to appropriate agent"""
        logger.debug(f"Parsing request: {state.get('query', '')[:80]}")
        
        action = state.get("action", "answer")
        
        # Route based on action
        if action == "summarize":
            return {"next": "summarize", **state}
        elif action == "quiz":
            return {"next": "quiz", **state}
        elif action == "cite":
            return {"next": "citations", **state}
        else:  # Default to research/answer
            return {"next": "research", **state}
    
    def _research_node(self, state: Dict) -> Dict:
        """Research/Q&A node"""
        logger.info(f"Research Node: Processing query")
        
        query = state.get("query", "")
        document_id = state.get("document_id")
        
        result = self.research_agent.answer_query(query, document_id)
        
        return {
            **state,
            "result": result,
            "sources": result.get("sources", [])
        }
    
    def _summarize_node(self, state: Dict) -> Dict:
        """Summarization node"""
        logger.info(f"Summarize Node: Processing")
        
        document_id = state.get("document_id")
        query = state.get("query")
        
        if document_id:
            result = self.summarizer_agent.summarize_document(document_id)
        elif query:
            result = self.summarizer_agent.summarize_query_results(query)
        else:
            result = {"status": "error", "message": "No document or query provided"}
        
        return {
            **state,
            "result": result
        }
    
    def _quiz_node(self, state: Dict) -> Dict:
        """Quiz generation node"""
        logger.info(f"Quiz Node: Processing")
        
        document_id = state.get("document_id")
        num_questions = state.get("num_questions", 5)
        require_approval = state.get("require_approval", True)
        
        if document_id:
            result = self.quiz_agent.generate_quiz(document_id, num_questions, require_approval)
        else:
            result = {"status": "error", "message": "Document ID required for quiz"}
        
        return {
            **state,
            "result": result
        }
    
    def _citations_node(self, state: Dict) -> Dict:
        """Citations node"""
        logger.info(f"Citations Node: Processing")
        
        query = state.get("query", "")
        document_id = state.get("document_id")
        
        result = self.citation_agent.get_citations_for_query(query, document_id)
        
        return {
            **state,
            "result": result,
            "sources": result.get("citations", [])
        }
    
    def _format_output(self, state: Dict) -> Dict:
        """Format final output"""
        logger.info(f"Format Output Node")
        
        return {
            **state,
            "formatted": True
        }
    
    def execute(self, query: str, action: str = "answer", document_id: Optional[str] = None, **kwargs) -> Dict:
        """
        Execute RAG workflow
        
        Args:
            query: User query
            action: "answer", "summarize", "quiz", or "cite"
            document_id: Optional document filter
            **kwargs: Additional parameters
            
        Returns:
            Dict with workflow result
        """
        try:
            logger.info(f"🚀 Executing RAG Workflow: action={action}")
            
            # Prepare input state
            input_state = {
                "query": query,
                "action": action,
                "document_id": document_id,
                "next": None,
                **kwargs
            }
            
            # Execute graph
            output = self.graph.invoke(input_state)
            
            logger.info(f"✅ Workflow completed")
            return output
        except Exception as e:
            logger.error(f"Workflow Error: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "result": None
            }
    
    def answer_question(self, query: str, document_id: Optional[str] = None) -> Dict:
        """Wrapper for Q&A workflow"""
        return self.execute(query, action="answer", document_id=document_id)
    
    def summarize(self, document_id: str) -> Dict:
        """Wrapper for summarization workflow"""
        return self.execute("", action="summarize", document_id=document_id)
    
    def generate_quiz(self, document_id: str, num_questions: int = 5, require_approval: bool = True) -> Dict:
        """Wrapper for quiz generation workflow"""
        return self.execute("", action="quiz", document_id=document_id, 
                          num_questions=num_questions, require_approval=require_approval)
    
    def get_citations(self, query: str, document_id: Optional[str] = None) -> Dict:
        """Wrapper for citations workflow"""
        return self.execute(query, action="cite", document_id=document_id)
    
    def process_document(self, document_id: str, text_content: str, page_num: int = 1) -> bool:
        """
        Process and embed a document
        
        Args:
            document_id: ID of document
            text_content: Full text content
            page_num: Page number for metadata
            
        Returns:
            True if successful
        """
        try:
            logger.info(f"Processing document: {document_id}")
            
            # Import chunker
            from app.services.chunker import TextProcessor
            chunker = TextProcessor()
            
            # Chunk text
            chunks = chunker.chunk_text(text_content, chunk_size=500, overlap=100)
            
            # Prepare chunks with embeddings
            chunks_with_embeddings = []
            for i, chunk_text in enumerate(chunks):
                embedding = self.embeddings.embed_text(chunk_text)
                chunks_with_embeddings.append({
                    "text": chunk_text,
                    "embedding": embedding,
                    "metadata": {
                        "page": page_num,
                        "chunk_number": i
                    }
                })
            
            # Store in vector DB
            success = self.vector_db.add_chunks(document_id, chunks_with_embeddings)
            
            if success:
                logger.info(f"✅ Document processed: {len(chunks_with_embeddings)} chunks embedded")
            
            return success
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            return False

