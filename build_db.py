import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from agent_system.setup_api import setup_embeddings
from pypdf import PdfReader


def main():
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build path to Data/books relative to the script location
    path = os.path.join(script_dir, "Data", "books")
    
    print(f"Looking for PDF files in: {path}")
    
    documents = []
    files = os.listdir(path)
    
    print(f"Files in directory: {files}")
    
    for filename in files:
        if filename.endswith(".pdf"):
            file_path = os.path.join(path, filename)
            print(f"Processing: {filename}")
            pdf = PdfReader(file_path)
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            documents.append({"text": text, "metadata": {"source": filename}})
    
    if not documents:
        print("No documents found in Data/books folder.")
        return
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    chunks = []
    for doc in documents:
        for chunk in text_splitter.split_text(doc["text"]):
            chunks.append({"text": chunk, "metadata": doc["metadata"]})
    
    embedding_model = setup_embeddings(model="models/text-embedding-004")
    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    
    # Also fix the path for the chroma_db directory
    persist_dir = os.path.join(script_dir, "Data", "chroma_db")
    vector_store = Chroma.from_texts(
        texts=texts,
        embedding=embedding_model,
        metadatas=metadatas,
        persist_directory=persist_dir
    )
    print(f"Chroma DB created at: {persist_dir}")

if __name__ == "__main__":
    main()

