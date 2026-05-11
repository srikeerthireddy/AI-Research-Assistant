"""
Quiz Agent - Generates quiz questions from research content.
Phase 8: Multi-Agent System with Human-in-the-Loop
"""
import logging
from typing import Dict, List, Optional

from app.services.retriever import RetrieverService
from app.services.generator import GeneratorService

logger = logging.getLogger(__name__)


class QuizAgent:
    """Agent for generating quizzes with human-in-the-loop approval"""
    
    def __init__(self):
        """Initialize quiz agent"""
        self.retriever = RetrieverService()
        self.generator = GeneratorService()
        self.pending_approvals = {}
    
    def generate_quiz(self, document_id: str, num_questions: int = 5, require_approval: bool = True) -> Dict:
        """
        Generate quiz questions from document
        
        Args:
            document_id: ID of document to generate quiz from
            num_questions: Number of questions to generate
            require_approval: If True, requires human approval (Human-in-the-Loop)
            
        Returns:
            Dict with quiz or approval request
        """
        try:
            logger.info(f"Quiz Agent: Generating {num_questions} questions from {document_id}")
            
            # Retrieve key content from document
            query = "important concepts definitions key terms"
            chunks = self.retriever.retrieve(query, top_k=20, document_id=document_id)
            
            if not chunks:
                return {"status": "error", "message": "No content to generate quiz"}
            
            # Combine content
            combined_content = "\\n\\n".join([c["text"] for c in chunks])
            
            # Generate questions
            questions = self.generator.generate_quiz_questions(combined_content, num_questions)
            
            if not questions:
                return {"status": "error", "message": "Failed to generate questions"}
            
            quiz_id = f"quiz_{document_id}_{len(self.pending_approvals)}"
            
            # HUMAN-IN-THE-LOOP: Require approval before finalizing
            if require_approval:
                self.pending_approvals[quiz_id] = {
                    "document_id": document_id,
                    "questions": questions,
                    "num_questions": len(questions),
                    "status": "pending_approval"
                }
                
                logger.info(f"✅ Quiz generated and waiting for approval: {quiz_id}")
                
                return {
                    "status": "pending_approval",
                    "quiz_id": quiz_id,
                    "document_id": document_id,
                    "preview_count": len(questions),
                    "message": "Quiz generated. Awaiting human approval before finalizing.",
                    "preview_questions": questions[:2]  # Show first 2 for preview
                }
            else:
                logger.info(f"✅ Quiz generated without approval: {num_questions} questions")
                return {
                    "status": "success",
                    "quiz_id": quiz_id,
                    "document_id": document_id,
                    "questions": questions,
                    "num_questions": len(questions)
                }
        except Exception as e:
            logger.error(f"Quiz Generation Error: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def approve_quiz(self, quiz_id: str) -> Dict:
        """
        Human approval for quiz
        
        Args:
            quiz_id: ID of quiz to approve
            
        Returns:
            Dict with approved quiz
        """
        if quiz_id not in self.pending_approvals:
            return {"status": "error", "message": "Quiz not found"}
        
        quiz_data = self.pending_approvals[quiz_id]
        del self.pending_approvals[quiz_id]
        
        logger.info(f"✅ Quiz approved by human: {quiz_id}")
        
        return {
            "status": "approved",
            "quiz_id": quiz_id,
            "document_id": quiz_data["document_id"],
            "questions": quiz_data["questions"],
            "num_questions": quiz_data["num_questions"]
        }
    
    def reject_quiz(self, quiz_id: str, reason: str = "") -> Dict:
        """
        Human rejection of quiz
        
        Args:
            quiz_id: ID of quiz to reject
            reason: Reason for rejection
            
        Returns:
            Dict confirming rejection
        """
        if quiz_id not in self.pending_approvals:
            return {"status": "error", "message": "Quiz not found"}
        
        del self.pending_approvals[quiz_id]
        
        logger.info(f"Quiz rejected by human: {quiz_id}. Reason: {reason}")
        
        return {
            "status": "rejected",
            "quiz_id": quiz_id,
            "reason": reason,
            "message": "Quiz rejected. Please generate a new one."
        }
    
    def get_pending_quizzes(self) -> Dict:
        """
        Get all pending quiz approvals
        
        Returns:
            Dict with pending quizzes
        """
        return {
            "status": "success",
            "pending_count": len(self.pending_approvals),
            "pending_quizzes": list(self.pending_approvals.keys())
        }
    
    def generate_quiz_for_query(self, query: str, document_id: Optional[str] = None, num_questions: int = 5) -> Dict:
        """
        Generate quiz based on query results
        
        Args:
            query: Query to base quiz on
            document_id: Optional filter to specific document
            num_questions: Number of questions
            
        Returns:
            Dict with quiz
        """
        try:
            logger.info(f"Quiz Agent: Generating quiz for query")
            
            # Retrieve chunks for query
            chunks = self.retriever.retrieve(query, top_k=10, document_id=document_id)
            
            if not chunks:
                return {"status": "error", "message": "No content found for query"}
            
            combined_content = "\\n\\n".join([c["text"] for c in chunks])
            questions = self.generator.generate_quiz_questions(combined_content, num_questions)
            
            return {
                "status": "success",
                "query": query,
                "questions": questions,
                "num_questions": len(questions)
            }
        except Exception as e:
            logger.error(f"Query-based Quiz Error: {str(e)}")
            return {"status": "error", "error": str(e)}
