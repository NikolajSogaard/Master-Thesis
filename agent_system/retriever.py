import os
from typing import List, Dict, Any
from .rag_system import initialize_rag_system, query_vector_store

class RagRetriever:
    """
    Retriever class that interfaces with the RAG system to provide relevant context 
    for the training program generator.
    """
    
    def __init__(self, db_name: str = os.path.join("Data", "chroma_db"), top_k: int = 5, rebuild_db: bool = False):
        """
        Initialize the RAG retriever.
        
        Args:
            db_name: Name of the vector database directory
            top_k: Number of top results to retrieve
            rebuild_db: Whether to rebuild the database from scratch
        """
        self.db_name = db_name
        self.top_k = top_k
        
        # Initialize the RAG system if rebuild_db is True
        if rebuild_db:
            print("Rebuilding RAG database...")
            success = initialize_rag_system()
            if not success:
                raise RuntimeError("Failed to initialize RAG system")
    
    def query(self, query_text: str) -> List[Dict[str, Any]]:
        """
        Query the vector store for relevant information.
        
        Args:
            query_text: The query text to search for
            
        Returns:
            List of relevant document chunks with metadata and similarity scores
        """
        return query_vector_store(query_text, k=self.top_k, persist_directory=self.db_name)
    
    def query_with_context(self, query_text: str) -> str:
        """
        Query the vector store and format the results into a context string.
        
        Args:
            query_text: The query text to search for
            
        Returns:
            Formatted context string with retrieved information
        """
        results = self.query(query_text)
        
        if not results:
            return "No relevant information found."
        
        context_parts = []
        for i, result in enumerate(results):
            context_parts.append(f"SOURCE {i+1}: {result['metadata']['filename']}")
            context_parts.append(f"EXCERPT: {result['text'][:500]}...")  # Limit text length
            context_parts.append(f"RELEVANCE: {result['similarity_score']:.4f}")
            context_parts.append("-" * 40)
        
        return "\n".join(context_parts)
