import os
import logging
from typing import List, Dict, Any
from langchain_chroma import Chroma  # Updated import to fix deprecation warning
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .setup_api import setup_embeddings, setup_llm

logger = logging.getLogger(__name__)

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
        
        # Setup summarization model
        self.summarize_model = setup_llm(
            model="gemini-2.0-flash", 
            temperature=0.2,
            respond_as_json=False
        )
        
        # Rebuild database if requested
        if rebuild_db:
            try:
                logger.info("Rebuilding RAG database...")
                self._build_database()
            except Exception as e:
                logger.error(f"Error rebuilding database: {e}")
        
        # Initialize the Chroma client with the updated import
        self.db = Chroma(
            persist_directory=self.db_name,
            embedding_function=self.embedding_model
        )
    
    def _build_database(self):
        """Build the vector database from documents in the data directory."""
        logger.info("Building database from documents...")
        
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
            logger.info("No documents found to build the database.")
            return
            
        logger.info(f"Loaded {len(documents)} documents.")
        
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        chunks = text_splitter.split_documents(documents)
        
        logger.info(f"Created {len(chunks)} chunks.")
        
        # Create and persist the database
        self.db = Chroma.from_documents(
            documents=chunks,
            embedding=self.embedding_model,
            persist_directory=self.db_name
        )
        self.db.persist()
        logger.info(f"Database built and persisted to {self.db_name}")
    
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
    
    def summarize_documents(self, documents: List[str], query: str) -> str:
        """
        Summarize retrieved documents into structured insights relevant to the query.
        
        Args:
            documents: List of text documents to summarize
            query: The original query to provide context
            
        Returns:
            Structured summary of key insights from the documents
        """
        if not documents:
            return ""
        
        # Combine documents but limit total length
        combined_text = "\n\n".join(doc[:3000] for doc in documents[:5])  # Limit size to avoid token limits
        
        summarization_prompt = f"""
        Below are excerpts from fitness and training resources related to: "{query}"
        
        EXCERPTS:
        {combined_text}
        
        Extract and organize the key insights from these excerpts into the following categories:
        
        1. TRAINING PRINCIPLES: Key training principles mentioned
        2. PROGRESSION STRATEGIES: How to progress in training (weight, reps, sets, RPE.)
        3. TRAINING INTENSITY: Recommendations for training intensity. Include Rate of Perceived Exertion (RPE) if available.
        4. EXERCISE SELECTION: Guidelines for selecting appropriate exercises 
        5. VOLUME & FREQUENCY: Recommendations for training volume and frequency
        
        For each category, provide 2-3 concise, actionable bullet points. If a category isn't addressed in the excerpts, write "No specific information available."
        
        Format your response in clear sections with bullet points. Focus on factual information, not opinions.
        """
        
        try:
            summary = self.summarize_model(summarization_prompt)
            # Validate the summary has the expected structure
            required_sections = ["TRAINING PRINCIPLES", "PROGRESSION STRATEGIES", "EXERCISE SELECTION"]
            if not any(section in summary for section in required_sections):
                logger.warning("Summary missing expected sections, may need reformatting")
            return summary
        except Exception as e:
            logger.error(f"Error in summarization: {e}")
            # More informative fallback with error details
            return f"Error generating summary: {str(e)[:100]}... Using raw excerpts instead."
    
    def query_with_context(self, query_text: str) -> str:
        """
        Query the vector store and format the results into a structured context string.
        
        Args:
            query_text: The query text to search for
            
        Returns:
            Formatted context string with retrieved information
        """
        results = self.query(query_text)
        
        if not results:
            return "No relevant information found."
        
        # Extract text content from results
        documents = [result["text"] for result in results]
        
        # Get source information for citation purposes
        sources = [result["metadata"].get("filename", "Unknown source") for result in results]
        unique_sources = list(set(sources))
        source_info = "SOURCES: " + ", ".join(unique_sources[:5])
        
        # Generate structured summary
        summary = self.summarize_documents(documents, query_text)
        
        if summary:
            return f"STRUCTURED KNOWLEDGE FOR TRAINING PROGRAM DESIGN:\n\n{summary}\n\n{source_info}"
        else:
            # Fallback to original format if summarization fails
            context_parts = []
            for i, result in enumerate(results):
                context_parts.append(f"SOURCE {i+1}: {result['metadata'].get('filename', 'Unknown')}")
                context_parts.append(f"EXCERPT: {result['text'][:500]}...")  # Limit text length
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
