import os
import sys
import PyPDF2
from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma  # Updated import

# Fix import issue by adding parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_system.setup_api import setup_embeddings

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text content as a string
    """
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            return text
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""

def process_directory(directory_path: str) -> List[Dict[str, Any]]:
    """
    Process all PDF files in a directory and extract text with metadata.
    
    Args:
        directory_path: Path to the directory containing PDF files
        
    Returns:
        List of dictionaries containing text content and metadata
    """
    documents = []
    
    for root, _, files in os.walk(directory_path):
        for file in files:
            if file.lower().endswith('.pdf'):
                pdf_path = os.path.join(root, file)
                text = extract_text_from_pdf(pdf_path)
                if text:
                    # Create metadata for the document
                    metadata = {
                        "source": pdf_path,
                        "filename": file,
                        "type": "book" if "books" in root.lower() else "training_program"
                    }
                    documents.append({"text": text, "metadata": metadata})
    
    return documents

def split_documents(documents: List[Dict[str, Any]], 
                    chunk_size: int = 1000, 
                    chunk_overlap: int = 200) -> List[Dict[str, Any]]:  
    """
    Split document text into smaller chunks for more effective embedding.
    
    Args:
        documents: List of documents with text and metadata
        chunk_size: Maximum size of each text chunk
        chunk_overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks with associated metadata
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    
    chunks = []
    for doc in documents:
        text_chunks = text_splitter.split_text(doc["text"])
        for chunk in text_chunks:
            chunks.append({"text": chunk, "metadata": doc["metadata"]})
    
    return chunks

def create_vector_store(chunks: List[Dict[str, Any]], persist_directory: str = os.path.join("Data", "chroma_db")):
    """
    Create and persist a vector store from document chunks.
    
    Args:
        chunks: List of text chunks with metadata
        persist_directory: Directory to store the vector database
        
    Returns:
        Chroma vector store instance
    """
    # Setup the embedding model
    embedding_model = setup_embeddings(model="models/text-embedding-004")
    
    # Prepare texts and metadatas for Chroma
    texts = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]
    
    # Create and persist the vector store
    vector_store = Chroma.from_texts(
        texts=texts,
        embedding=embedding_model,
        metadatas=metadatas,
        persist_directory=persist_directory
    )
    
    vector_store.persist()
    print(f"Vector store created and persisted at {persist_directory}")
    return vector_store

def query_vector_store(query: str, k: int = 5, persist_directory: str = os.path.join("Data", "chroma_db")):
    """
    Query the vector store for relevant document chunks.
    
    Args:
        query: The query text to search for
        k: Number of results to return
        persist_directory: Directory where the vector store is persisted
        
    Returns:
        List of relevant document chunks with similarity scores
    """
    # Setup the embedding model
    embedding_model = setup_embeddings(model="models/text-embedding-004")
    
    # Load the existing vector store
    vector_store = Chroma(
        persist_directory=persist_directory,
        embedding_function=embedding_model
    )
    
    # Query the vector store
    results = vector_store.similarity_search_with_score(query, k=k)
    
    # Format the results
    formatted_results = []
    for doc, score in results:
        formatted_results.append({
            "text": doc.page_content,
            "metadata": doc.metadata,
            "similarity_score": score
        })
    
    return formatted_results

def initialize_rag_system():
    """
    Initialize the RAG system by processing documents and creating the vector store.
    
    Returns:
        True if initialization was successful, False otherwise
    """
    try:
        # Process books and training programs - fix the path for sub_books
        books_path = "sub_books"  # Changed from os.path.join("books", "sub_books")
        training_programs_path = "Training_programs"
        
        print(f"Processing documents from {books_path}...")
        books_docs = process_directory(books_path)
        
        print(f"Processing documents from {training_programs_path}...")
        training_docs = process_directory(training_programs_path)
        
        all_documents = books_docs + training_docs
        print(f"Total documents processed: {len(all_documents)}")
        
        # Split documents into chunks
        print("Splitting documents into chunks...")
        chunks = split_documents(all_documents)
        print(f"Total chunks created: {len(chunks)}")
        
        # Create and persist vector store
        print("Creating vector store...")
        create_vector_store(chunks)
        
        return True
    except Exception as e:
        print(f"Error initializing RAG system: {e}")
        return False

if __name__ == "__main__":
    # Initialize the RAG system
    success = initialize_rag_system()
    if (success):
        print("RAG system initialized successfully!")
        
        # Test query
        test_query = "What is the most important factors for progressive overload"
        print(f"\nTesting query: '{test_query}'")
        results = query_vector_store(test_query)
        
        print(f"Found {len(results)} relevant chunks:")
        for i, result in enumerate(results):
            print(f"\nResult {i+1} (Score: {result['similarity_score']:.4f})")
            print(f"Source: {result['metadata']['source']}")
            print(f"Text: {result['text'][:200]}...")
    else:
        print("Failed to initialize RAG system.")
