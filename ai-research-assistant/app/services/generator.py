"""
Generator Service - Generates responses and content using LLMs.
Phase 7: Generation with hallucination prevention through context-only answers
"""
import logging
from typing import List, Dict, Optional
from openai import OpenAI

from app.config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)


class GeneratorService:
    """Generate responses from retrieved context to prevent hallucination"""
    
    def __init__(self, model: str = OPENAI_MODEL):
        """
        Initialize generator with OpenAI client
        
        Args:
            model: OpenAI model to use
        """
        self.model = model
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        logger.info(f"✅ Generator initialized with model: {model}")
    
    def generate_answer(self, query: str, context: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate answer based on retrieved context only
        (Prevents hallucination by constraining to context)
        
        Args:
            query: User's question
            context: Retrieved context from documents
            system_prompt: Optional custom system prompt
            
        Returns:
            Generated answer based only on context
        """
        if not system_prompt:
            system_prompt = """You are a helpful research assistant. Answer questions ONLY based on the provided context.
            
IMPORTANT RULES:
1. Only use information from the provided context
2. If the answer is not in the context, say "I don't have information about this in the provided documents"
3. Always cite which source/document the information comes from
4. Be accurate and concise
5. Do not make up or infer information not explicitly stated"""
        
        try:
            logger.info(f"Generating answer for: {query[:80]}...")
            
            messages = [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": f"Context from documents:\n{context}\n\nQuestion: {query}"
                }
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            answer = response.choices[0].message.content
            logger.info(f"✅ Answer generated ({len(answer)} chars)")
            return answer
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return f"Error generating answer: {str(e)}"
    
    def generate_summary(self, content: str, length: str = "concise") -> str:
        """
        Generate a summary of the content
        
        Args:
            content: Content to summarize
            length: "concise", "moderate", or "detailed"
            
        Returns:
            Generated summary
        """
        length_map = {
            "concise": "2-3 sentences",
            "moderate": "3-5 sentences",
            "detailed": "1-2 paragraphs"
        }
        
        system_prompt = f"""You are a professional summarizer. Create a {length_map.get(length, 'concise')} summary of the provided content.
        
- Keep the summary accurate and informative
- Maintain key points and details
- Use clear, professional language"""
        
        try:
            logger.info(f"Generating {length} summary...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Content to summarize:\n{content}"}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            summary = response.choices[0].message.content
            logger.info(f"✅ Summary generated")
            return summary
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            return f"Error: {str(e)}"
    
    def generate_quiz_questions(self, content: str, num_questions: int = 5) -> List[Dict]:
        """
        Generate multiple-choice quiz questions from content
        
        Args:
            content: Content to generate questions from
            num_questions: Number of questions to generate
            
        Returns:
            List of quiz questions with options and answers
        """
        system_prompt = f"""You are an expert quiz creator. Generate exactly {num_questions} multiple-choice questions based on the provided content.

For each question, provide:
1. Question text
2. Four options (A, B, C, D)
3. Correct answer (A, B, C, or D)
4. Explanation

Format as JSON array with structure:
[
  {{
    "question": "Question text?",
    "options": {{"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}},
    "correct_answer": "A",
    "explanation": "Why this is correct..."
  }}
]"""
        
        try:
            logger.info(f"Generating {num_questions} quiz questions...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Content:\n{content}"}
                ],
                temperature=0.8,
                max_tokens=2000
            )
            
            # Parse JSON response
            import json
            response_text = response.choices[0].message.content
            
            # Extract JSON from response
            try:
                questions = json.loads(response_text)
            except:
                # Try to extract JSON if there's extra text
                import re
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    questions = json.loads(json_match.group())
                else:
                    logger.error("Could not parse quiz questions")
                    return []
            
            logger.info(f"✅ Generated {len(questions)} quiz questions")
            return questions
        except Exception as e:
            logger.error(f"Error generating quiz: {str(e)}")
            return []
    
    def extract_topics(self, content: str) -> List[str]:
        """
        Extract important topics from content
        
        Args:
            content: Content to extract topics from
            
        Returns:
            List of key topics
        """
        system_prompt = """You are an expert topic extractor. Identify and list the most important topics/concepts from the provided content.

Return as a JSON array of strings:
["Topic 1", "Topic 2", "Topic 3", ...]

List only the key concepts, not too granular."""
        
        try:
            logger.info("Extracting topics...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Content:\n{content}"}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            import json
            response_text = response.choices[0].message.content
            
            try:
                topics = json.loads(response_text)
            except:
                import re
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    topics = json.loads(json_match.group())
                else:
                    topics = []
            
            logger.info(f"✅ Extracted {len(topics)} topics")
            return topics
        except Exception as e:
            logger.error(f"Error extracting topics: {str(e)}")
            return []

