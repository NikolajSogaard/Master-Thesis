import os
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .setup_api import setup_embeddings

class RagRetriever:
    def __init__(self, db_name="chroma_db", top_k=5, rebuild_db=False):
        """
        Initialize the RAG retriever with a Chroma database.
        
        Args:
            db_name: Path to the database
            top_k: Number of documents to retrieve
            rebuild_db: Whether to rebuild the database
        """
        self.db_name = db_name
        self.top_k = top_k
        
        try:
            self.embedding_function = setup_embeddings()
            
            # Create the database directory if it doesn't exist
            os.makedirs(os.path.dirname(self.db_name), exist_ok=True)
            
            # Initialize or load the database
            if rebuild_db or not os.path.exists(self.db_name):
                self._build_database()
            else:
                self.db = Chroma(
                    persist_directory=self.db_name,
                    embedding_function=self.embedding_function
                )
        except Exception as e:
            print(f"Error initializing RAG retriever: {e}")
            raise
    
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
            embedding=self.embedding_function,
            persist_directory=self.db_name
        )
        self.db.persist()
        print(f"Database built and persisted to {self.db_name}")
    
    def retrieve(self, query, top_k=None):
        """
        Retrieve relevant documents for a query.
        
        Args:
            query: The query string
            top_k: Optional override for number of documents to retrieve
            
        Returns:
            List of retrieved documents
        """
        if top_k is None:
            top_k = self.top_k
            
        results = self.db.similarity_search(query, k=top_k)
        return [doc.page_content for doc in results]
