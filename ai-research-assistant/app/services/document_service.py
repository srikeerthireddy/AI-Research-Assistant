"""
Document Service - Handles document upload and storage
"""
from typing import Dict, List, Optional
from pathlib import Path
import uuid
import json
import logging
from datetime import datetime
from app.config import UPLOADS_DIR, MAX_FILE_SIZE_BYTES, ALLOWED_EXTENSIONS

logger = logging.getLogger(__name__)


class DocumentService:
    """Service for managing document uploads and metadata"""
    
    def __init__(self):
        self.uploads_dir = Path(UPLOADS_DIR)
        self.uploads_dir.mkdir(exist_ok=True)
        self.metadata_file = self.uploads_dir / "metadata.json"
        self.documents = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load document metadata from file"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load metadata: {e}")
        return {}
    
    def _save_metadata(self):
        """Save document metadata to file"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.documents, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def validate_upload(self, filename: str, file_size: int) -> tuple[bool, str]:
        """
        Validate file before upload
        
        Returns:
            (is_valid, error_message)
        """
        # Check file extension
        file_ext = Path(filename).suffix.lower().lstrip(".")
        if file_ext not in ALLOWED_EXTENSIONS:
            ext_list = ", ".join(sorted(ALLOWED_EXTENSIONS))
            return False, f"File type '.{file_ext}' not allowed. Allowed: {ext_list}"
        
        # Check file size
        if file_size > MAX_FILE_SIZE_BYTES:
            max_mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)
            return False, f"File size exceeds {max_mb:.0f}MB limit"
        
        return True, ""
    
    def save_document(self, filename: str, file_content: bytes) -> Dict:
        """
        Save uploaded document
        
        Returns:
            Dictionary with document metadata
        """
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Save file with unique name
        file_ext = Path(filename).suffix.lower()
        safe_filename = f"{document_id}{file_ext}"
        file_path = self.uploads_dir / safe_filename
        
        # Write file
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Create metadata
        metadata = {
            "document_id": document_id,
            "original_filename": filename,
            "saved_filename": safe_filename,
            "file_size": len(file_content),
            "file_extension": file_ext,
            "upload_time": datetime.now().isoformat(),
            "status": "uploaded"
        }
        
        # Store metadata
        self.documents[document_id] = metadata
        self._save_metadata()
        
        logger.info(f"Document {document_id} uploaded: {filename}")
        
        return metadata
    
    def get_document(self, document_id: str) -> Optional[Dict]:
        """Get document metadata"""
        return self.documents.get(document_id)
    
    def get_document_path(self, document_id: str) -> Optional[Path]:
        """Get file path for a document"""
        metadata = self.get_document(document_id)
        if not metadata:
            return None
        
        file_path = self.uploads_dir / metadata['saved_filename']
        if file_path.exists():
            return file_path
        
        return None
    
    def list_documents(self) -> List[Dict]:
        """List all uploaded documents"""
        return list(self.documents.values())
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document"""
        metadata = self.get_document(document_id)
        if not metadata:
            return False
        
        # Delete file
        file_path = self.uploads_dir / metadata['saved_filename']
        if file_path.exists():
            file_path.unlink()
        
        # Remove from metadata
        del self.documents[document_id]
        self._save_metadata()
        
        logger.info(f"Document {document_id} deleted")
        return True
