import os
from typing import List, Dict, Any
from langchain_chroma import Chroma  # Updated import to fix deprecation warning
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .setup_api import setup_embeddings

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
        
        # Setup embedding model
        self.embedding_model = setup_embeddings(model="models/text-embedding-004")
        
        # Rebuild database if requested
        if rebuild_db:
            try:
                print("Rebuilding RAG database...")
                self._build_database()
            except Exception as e:
                print(f"Error rebuilding database: {e}")
        
        # Initialize the Chroma client with the updated import
        self.db = Chroma(
            persist_directory=self.db_name,
            embedding_function=self.embedding_model
        )
    
    def _build_database(self):
        """Build the vector database from documents in the data directory."""
        print("Building database from documents...")
        
        # Define the data directory
        data_dir = os.path.join('Data', 'documents')
        
        # Load documents
        loader = DirectoryLoader(
            data_dir,
            glob="**/*.txt", 
            loader_cls=TextLoader
        )
        documents = loader.load()
        
        if not documents:
            print("No documents found to build the database.")
            return
            
        print(f"Loaded {len(documents)} documents.")
        
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_documents(documents)
        
        print(f"Created {len(chunks)} chunks.")
        
        # Create and persist the database
        self.db = Chroma.from_documents(
            documents=chunks,
            embedding=self.embedding_model,
            persist_directory=self.db_name
        )
        self.db.persist()
        print(f"Database built and persisted to {self.db_name}")
    
    def query(self, query_text: str) -> List[Dict[str, Any]]:
        """
        Query the vector store for relevant information.
        
        Args:
            query_text: The query text to search for
            
        Returns:
            List of relevant document chunks with metadata and similarity scores
        """
        results = self.db.similarity_search_with_score(query_text, k=self.top_k)
        
        # Format the results
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "text": doc.page_content,
                "metadata": doc.metadata,
                "similarity_score": score
            })
        
        return formatted_results
    
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
            context_parts.append(f"SOURCE {i+1}: {result['metadata'].get('filename', 'Unknown')}")
            context_parts.append(f"EXCERPT: {result['text'][:500]}...")  # Limit text length
            context_parts.append(f"RELEVANCE: {result['similarity_score']:.4f}")
            context_parts.append("-" * 40)
        
        return "\n".join(context_parts)
        
    def retrieve(self, query_text: str) -> List[str]:
        """
        Alias for query method returning only the text content.
        
        Args:
            query_text: The query text to search for
            
        Returns:
            List of text content from retrieved documents
        """
        results = self.query(query_text)
        return [result["text"] for result in results]
