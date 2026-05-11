"""
Text Processor Service
Handles text cleaning, structure detection, summarization, and intelligent chunking.
"""
from typing import Dict, List, Optional
import re
import logging

logger = logging.getLogger(__name__)


class TextProcessor:
    """Process and analyze extracted text."""
    
    def __init__(self):
        self.section_patterns = [
            r'^#{1,6}\s+(.+)$',  # Markdown headers
            r'^([A-Z][A-Z\s]+)$',  # ALL CAPS headings
            r'^[\d]+\.?\s+(.+)$',  # Numbered sections
            r'^(chapter|section|part)\s+\d+[\.:\-\s].+$',  # Common headings
        ]
        self.stop_words = {
            "the", "and", "for", "that", "with", "this", "from", "have", "are",
            "was", "were", "will", "shall", "would", "should", "could", "into",
            "about", "than", "then", "them", "they", "their", "there", "here",
            "your", "you", "our", "out", "all", "any", "can", "not", "but",
            "has", "had", "been", "its", "also", "such", "very", "more", "most",
        }
    
    def process_text(self, text: str) -> Dict:
        """
        Process text and extract structural information
        
        Returns:
        {
            "processed_text": "...",
            "sections": [...],
            "summary": "...",
            "statistics": {...}
        }
        """
        if not text:
            return {"error": "Empty text"}
        
        # Extract sections
        sections = self._extract_sections(text)
        
        # Generate summary
        summary = self._generate_summary(text)
        
        # Calculate statistics
        statistics = self._calculate_statistics(text)
        
        return {
            "processed_text": text,
            "sections": sections,
            "summary": summary,
            "statistics": statistics,
            "language_info": self._detect_language_info(text)
        }
    
    def _extract_sections(self, text: str) -> List[Dict]:
        """Extract logical sections from text"""
        sections = []
        
        # Split by double newlines (paragraphs)
        paragraphs = text.split('\n\n')
        
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if not para or len(para) < 20:
                continue
            
            # Check if this looks like a heading
            is_heading = any(re.match(pattern, para) for pattern in self.section_patterns)
            
            sections.append({
                "id": i,
                "type": "heading" if is_heading else "paragraph",
                "text": para,
                "length": len(para),
                "word_count": len(para.split()),
                "sentences": len(re.split(r'[.!?]+', para))
            })
        
        return sections
    
    def _generate_summary(self, text: str, sentences_count: int = 3) -> str:
        """Generate extractive summary"""
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) <= sentences_count:
            return text
        
        # Simple scoring based on word frequency
        words = text.lower().split()
        word_freq = {}
        
        for word in words:
            word = re.sub(r'[^\w]', '', word)
            if len(word) > 3:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Score sentences
        scored_sentences = []
        for sent in sentences:
            score = 0
            words_in_sent = sent.lower().split()
            for word in words_in_sent:
                word = re.sub(r'[^\w]', '', word)
                score += word_freq.get(word, 0)
            
            scored_sentences.append((sent, score))
        
        # Get top sentences
        top_sentences = sorted(scored_sentences, key=lambda x: x[1], reverse=True)[:sentences_count]
        
        # Sort by original order
        summary = ' '.join([s[0] for s in sorted(top_sentences, key=lambda x: sentences.index(x[0]))])
        
        return summary + "."
    
    def _calculate_statistics(self, text: str) -> Dict:
        """Calculate text statistics"""
        if not text:
            return {}
        
        words = text.split()
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        # Character counts
        letters = sum(1 for c in text if c.isalpha())
        digits = sum(1 for c in text if c.isdigit())
        spaces = sum(1 for c in text if c.isspace())
        special = len(text) - letters - digits - spaces
        
        # Readability metrics
        avg_word_length = sum(len(w) for w in words) / len(words) if words else 0
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        
        return {
            "characters": len(text),
            "words": len(words),
            "sentences": len(sentences),
            "paragraphs": len(text.split('\n\n')),
            "letters": letters,
            "digits": digits,
            "spaces": spaces,
            "special_chars": special,
            "avg_word_length": round(avg_word_length, 2),
            "avg_sentence_length": round(avg_sentence_length, 2),
            "unique_words": len(set(w.lower() for w in words))
        }
    
    def _detect_language_info(self, text: str) -> Dict:
        """Detect language and writing information"""
        info = {
            "has_numbers": bool(re.search(r'\d', text)),
            "has_urls": bool(re.search(r'http[s]?://', text)),
            "has_emails": bool(re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)),
            "code_likelihood": self._detect_code(text)
        }
        return info
    
    def _detect_code(self, text: str) -> float:
        """Estimate likelihood of code presence (0-1)"""
        code_indicators = [
            r'def\s+\w+\(',
            r'class\s+\w+',
            r'import\s+\w+',
            r'\{.*\}',
            r'<\w+>.*</\w+>',
            r'^\s+[a-z_]+\s*=',
        ]
        
        matches = sum(1 for pattern in code_indicators if re.search(pattern, text))
        return min(1.0, matches / len(code_indicators))
    
    def split_into_chunks(self, text: str, chunk_size: int = 1000, 
                         overlap: int = 100) -> List[Dict]:
        """
        Split text into chunks with overlap
        
        Returns:
        [{
            "chunk_id": 0,
            "text": "...",
            "start": 0,
            "end": 1000,
            "word_count": 150
        }]
        """
        chunks = []
        chunk_id = 0
        
        for i in range(0, len(text), chunk_size - overlap):
            chunk_text = text[i:i + chunk_size]
            
            chunks.append({
                "chunk_id": chunk_id,
                "text": chunk_text,
                "start_char": i,
                "end_char": i + len(chunk_text),
                "length": len(chunk_text),
                "word_count": len(chunk_text.split())
            })
            chunk_id += 1
        
        return chunks

    def split_into_semantic_chunks(
        self,
        text: str,
        target_chunk_size: int = 1000,
        min_chunk_size: int = 350,
        overlap: int = 120,
        respect_headers: bool = True,
    ) -> Dict:
        """
        Phase 3 intelligent chunking.

        Splits by semantic blocks (paragraphs/headings), preserves section boundaries,
        and adds chunk relationship metadata for retrieval pipelines.
        """
        if not text or not text.strip():
            return {
                "chunks": [],
                "strategy": "semantic_v1",
                "metadata": {"reason": "empty_text"},
            }

        clean_text = text.replace("\r\n", "\n").strip()
        blocks = self._build_semantic_blocks(clean_text, respect_headers=respect_headers)
        chunks = self._assemble_semantic_chunks(
            blocks=blocks,
            target_chunk_size=target_chunk_size,
            min_chunk_size=min_chunk_size,
            overlap=overlap,
        )

        self._link_chunk_relationships(chunks)

        return {
            "chunks": chunks,
            "strategy": "semantic_v1",
            "metadata": {
                "target_chunk_size": target_chunk_size,
                "min_chunk_size": min_chunk_size,
                "overlap": overlap,
                "respect_headers": respect_headers,
                "total_blocks": len(blocks),
                "total_chunks": len(chunks),
            },
        }

    def _is_heading(self, paragraph: str) -> bool:
        text = paragraph.strip()
        if not text:
            return False

        if any(re.match(pattern, text, re.IGNORECASE) for pattern in self.section_patterns):
            return True

        # Heuristic: short line, title case / numbered section style.
        if len(text) <= 90 and not re.search(r"[.!?]", text):
            words = text.split()
            if 1 <= len(words) <= 10:
                title_like = sum(1 for w in words if w[:1].isupper())
                return title_like >= max(1, len(words) // 2)

        return False

    def _build_semantic_blocks(self, text: str, respect_headers: bool) -> List[Dict]:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n+", text) if p.strip()]
        blocks: List[Dict] = []
        current_section = "Untitled"
        char_cursor = 0

        for para in paragraphs:
            is_heading = respect_headers and self._is_heading(para)

            if is_heading:
                current_section = para[:120]
                blocks.append(
                    {
                        "type": "heading",
                        "text": para,
                        "section_title": current_section,
                        "start_char": char_cursor,
                        "end_char": char_cursor + len(para),
                    }
                )
            else:
                blocks.append(
                    {
                        "type": "paragraph",
                        "text": para,
                        "section_title": current_section,
                        "start_char": char_cursor,
                        "end_char": char_cursor + len(para),
                    }
                )

            char_cursor += len(para) + 2

        return blocks

    def _assemble_semantic_chunks(
        self,
        blocks: List[Dict],
        target_chunk_size: int,
        min_chunk_size: int,
        overlap: int,
    ) -> List[Dict]:
        chunks: List[Dict] = []
        current_blocks: List[Dict] = []
        chunk_id = 0

        def finalize_chunk() -> None:
            nonlocal chunk_id
            if not current_blocks:
                return

            merged_text = "\n\n".join(block["text"] for block in current_blocks).strip()
            if not merged_text:
                return

            start_char = current_blocks[0]["start_char"]
            end_char = current_blocks[-1]["end_char"]
            section_title = current_blocks[-1].get("section_title", "Untitled")
            heading_count = sum(1 for b in current_blocks if b["type"] == "heading")

            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "text": merged_text,
                    "start_char": start_char,
                    "end_char": end_char,
                    "length": len(merged_text),
                    "word_count": len(merged_text.split()),
                    "section_title": section_title,
                    "heading_count": heading_count,
                    "block_count": len(current_blocks),
                    "keywords": self._extract_keywords(merged_text, top_k=6),
                }
            )
            chunk_id += 1

        for block in blocks:
            candidate = current_blocks + [block]
            candidate_text = "\n\n".join(b["text"] for b in candidate)

            should_split = False
            if current_blocks and len(candidate_text) > target_chunk_size:
                should_split = True

            # Start a new chunk when a new heading appears and current chunk is already meaningful.
            if (
                current_blocks
                and block["type"] == "heading"
                and len("\n\n".join(b["text"] for b in current_blocks)) >= min_chunk_size
            ):
                should_split = True

            if should_split:
                finalize_chunk()
                previous_text = chunks[-1]["text"] if chunks else ""
                current_blocks = []

                if overlap > 0 and previous_text:
                    overlap_text = self._tail_words(previous_text, overlap)
                    if overlap_text:
                        current_blocks.append(
                            {
                                "type": "overlap",
                                "text": overlap_text,
                                "section_title": block.get("section_title", "Untitled"),
                                "start_char": max(0, block["start_char"] - len(overlap_text)),
                                "end_char": block["start_char"],
                            }
                        )

            current_blocks.append(block)

        finalize_chunk()
        return chunks

    def _tail_words(self, text: str, overlap_chars: int) -> str:
        if overlap_chars <= 0 or not text:
            return ""

        snippet = text[-overlap_chars:].strip()
        if not snippet:
            return ""

        # Align to nearest word boundary at the beginning.
        first_space = snippet.find(" ")
        if 0 <= first_space < len(snippet) - 1:
            snippet = snippet[first_space + 1 :].strip()

        return snippet

    def _extract_keywords(self, text: str, top_k: int = 6) -> List[str]:
        words = re.findall(r"[A-Za-z][A-Za-z\-']{2,}", text.lower())
        freq: Dict[str, int] = {}

        for word in words:
            if word in self.stop_words:
                continue
            freq[word] = freq.get(word, 0) + 1

        ranked = sorted(freq.items(), key=lambda item: item[1], reverse=True)
        return [word for word, _ in ranked[:top_k]]

    def _link_chunk_relationships(self, chunks: List[Dict]) -> None:
        for i, chunk in enumerate(chunks):
            chunk["prev_chunk_id"] = i - 1 if i > 0 else None
            chunk["next_chunk_id"] = i + 1 if i < len(chunks) - 1 else None
            chunk["topic_signature"] = " | ".join(chunk.get("keywords", [])[:3])

