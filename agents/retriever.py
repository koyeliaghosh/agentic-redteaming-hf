"""
RetrieverAgent: Manages embeddings and knowledge retrieval using FAISS.
Provides context for attack planning and evaluation.
"""

import os
import json
import logging
import pickle
from typing import List, Dict, Any, Optional
import numpy as np
import faiss

from utils.hf_client import HuggingFaceClient, HuggingFaceAPIError
from config import Config

logger = logging.getLogger(__name__)


class Document:
    """Represents a document stored in the vector store."""
    
    def __init__(
        self,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a document.
        
        Args:
            doc_id: Unique identifier for the document
            text: Text content of the document
            metadata: Optional metadata dictionary
        """
        self.doc_id = doc_id
        self.text = text
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary."""
        return {
            "doc_id": self.doc_id,
            "text": self.text,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Document":
        """Create document from dictionary."""
        return cls(
            doc_id=data["doc_id"],
            text=data["text"],
            metadata=data.get("metadata", {})
        )


class RetrieverAgent:
    """
    Manages embeddings and knowledge retrieval using FAISS.
    Provides context for attack planning and evaluation.
    """
    
    def __init__(self, config: Config):
        """
        Initialize RetrieverAgent with FAISS index.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.hf_client = HuggingFaceClient(
            api_key=config.huggingface_api_key,
            base_url=config.hf_base_url,
            max_retries=config.max_retries
        )
        self.embed_model = config.hf_embed_model
        
        # Initialize FAISS index and document store
        self.index: Optional[faiss.Index] = None
        self.document_store: Dict[int, Document] = {}
        self.embedding_dimension: Optional[int] = None
        
        # Load or create index
        self.index = self._load_or_create_index()
        
        logger.info(
            f"RetrieverAgent initialized with model {self.embed_model}, "
            f"index size: {self.index.ntotal if self.index else 0}"
        )
    
    async def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding vector for text using Hugging Face embeddings.
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector as numpy array
            
        Raises:
            HuggingFaceAPIError: On API errors
        """
        try:
            # Generate embedding using HF client
            embedding_list = self.hf_client.generate_embedding(
                model=self.embed_model,
                text=text
            )
            
            # Convert to numpy array
            embedding = np.array(embedding_list, dtype=np.float32)
            
            # Set embedding dimension on first call
            if self.embedding_dimension is None:
                self.embedding_dimension = len(embedding)
                logger.info(f"Embedding dimension set to {self.embedding_dimension}")
            
            # Validate dimension consistency
            if len(embedding) != self.embedding_dimension:
                raise ValueError(
                    f"Embedding dimension mismatch: expected {self.embedding_dimension}, "
                    f"got {len(embedding)}"
                )
            
            return embedding
            
        except HuggingFaceAPIError as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during embedding generation: {str(e)}")
            raise
    
    async def add_documents(self, documents: List[Document]) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of Document objects to add
            
        Raises:
            ValueError: If documents list is empty
            HuggingFaceAPIError: On embedding generation errors
        """
        if not documents:
            raise ValueError("Cannot add empty document list")
        
        logger.info(f"Adding {len(documents)} documents to vector store")
        
        try:
            # Generate embeddings for all documents
            embeddings = []
            for doc in documents:
                embedding = await self.embed_text(doc.text)
                embeddings.append(embedding)
            
            # Convert to numpy array
            embeddings_array = np.array(embeddings, dtype=np.float32)
            
            # Get current index size to calculate new IDs
            current_size = self.index.ntotal
            
            # Add embeddings to FAISS index
            self.index.add(embeddings_array)
            
            # Store documents with their index IDs
            for i, doc in enumerate(documents):
                doc_index_id = current_size + i
                self.document_store[doc_index_id] = doc
            
            logger.info(
                f"Successfully added {len(documents)} documents. "
                f"Total documents: {self.index.ntotal}"
            )
            
            # Save index after adding documents
            self.save_index(self.config.faiss_index_path)
            
        except Exception as e:
            logger.error(f"Failed to add documents: {str(e)}")
            raise
    
    async def search(self, query: str, top_k: int = 5) -> List[Document]:
        """
        Retrieve most similar documents using similarity search.
        
        Args:
            query: Query text to search for
            top_k: Number of top results to return (default: 5)
            
        Returns:
            List of most similar Document objects
            
        Raises:
            ValueError: If index is empty or top_k is invalid
            HuggingFaceAPIError: On embedding generation errors
        """
        if self.index.ntotal == 0:
            logger.warning("Search called on empty index")
            return []
        
        if top_k <= 0:
            raise ValueError(f"top_k must be positive, got {top_k}")
        
        # Limit top_k to available documents
        top_k = min(top_k, self.index.ntotal)
        
        logger.debug(f"Searching for top {top_k} similar documents")
        
        try:
            # Generate embedding for query
            query_embedding = await self.embed_text(query)
            
            # Reshape for FAISS (expects 2D array)
            query_embedding = query_embedding.reshape(1, -1)
            
            # Search FAISS index
            distances, indices = self.index.search(query_embedding, top_k)
            
            # Retrieve documents
            results = []
            for idx in indices[0]:
                if idx in self.document_store:
                    results.append(self.document_store[idx])
                else:
                    logger.warning(f"Document with index {idx} not found in store")
            
            logger.debug(f"Found {len(results)} matching documents")
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            raise
    
    def save_index(self, path: str) -> None:
        """
        Persist FAISS index and document store to local disk.
        
        Args:
            path: Directory path to save index files
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(path, exist_ok=True)
            
            # Save FAISS index
            index_file = os.path.join(path, "faiss.index")
            faiss.write_index(self.index, index_file)
            
            # Save document store
            store_file = os.path.join(path, "document_store.pkl")
            with open(store_file, "wb") as f:
                pickle.dump(self.document_store, f)
            
            # Save metadata
            metadata_file = os.path.join(path, "metadata.json")
            metadata = {
                "embedding_dimension": self.embedding_dimension,
                "embed_model": self.embed_model,
                "total_documents": self.index.ntotal
            }
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Index saved to {path} ({self.index.ntotal} documents)")
            
        except Exception as e:
            logger.error(f"Failed to save index: {str(e)}")
            raise
    
    def _load_or_create_index(self) -> faiss.Index:
        """
        Load existing FAISS index or create a new one.
        Handles index corruption gracefully by recreating.
        
        Returns:
            FAISS Index object
        """
        index_path = self.config.faiss_index_path
        index_file = os.path.join(index_path, "faiss.index")
        store_file = os.path.join(index_path, "document_store.pkl")
        metadata_file = os.path.join(index_path, "metadata.json")
        
        # Try to load existing index
        if os.path.exists(index_file) and os.path.exists(store_file):
            try:
                logger.info(f"Loading existing FAISS index from {index_path}")
                
                # Load metadata
                if os.path.exists(metadata_file):
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)
                        self.embedding_dimension = metadata.get("embedding_dimension")
                        logger.info(f"Loaded metadata: {metadata}")
                
                # Load FAISS index
                index = faiss.read_index(index_file)
                
                # Load document store
                with open(store_file, "rb") as f:
                    self.document_store = pickle.load(f)
                
                logger.info(
                    f"Successfully loaded index with {index.ntotal} documents"
                )
                return index
                
            except Exception as e:
                logger.warning(
                    f"Failed to load existing index (corruption detected): {str(e)}. "
                    "Creating new index."
                )
                # Fall through to create new index
        
        # Create new index
        logger.info("Creating new FAISS index")
        
        # We'll create the index with a default dimension
        # It will be properly initialized when first embedding is generated
        # For now, use a common dimension (384 for all-MiniLM-L6-v2)
        default_dimension = 384
        
        # Create IndexFlatL2 for exact L2 distance search
        index = faiss.IndexFlatL2(default_dimension)
        self.embedding_dimension = default_dimension
        
        logger.info(f"Created new FAISS IndexFlatL2 with dimension {default_dimension}")
        
        # Create directory for index storage
        os.makedirs(index_path, exist_ok=True)
        
        return index
    
    def close(self):
        """Clean up resources."""
        if self.hf_client:
            self.hf_client.close()
        logger.debug("RetrieverAgent closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
