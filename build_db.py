import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from agent_system.setup_api import setup_embeddings
from pypdf import PdfReader


def main():
    path = os.path.join("Data", "books")
    if not os.path.exists(path):
        print(f"Directory '{path}' not found. Please create it and add PDF files.")
        return
        
    documents = []
    for filename in os.listdir(path):
        if filename.endswith(".pdf"):
            file_path = os.path.join(path, filename)
            try:
                pdf = PdfReader(file_path)
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                documents.append({"text": text, "metadata": {"source": filename}})
                print(f"Successfully processed: {filename}")
            except FileNotFoundError:
                print(f"File not found: {file_path}")
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
    
    if not documents:
        print("No documents found or processed in data/books folder.")
        return
    
    print(f"Processing {len(documents)} documents...")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    chunks = []
    for doc in documents:
        for chunk in text_splitter.split_text(doc["text"]):
            chunks.append({"text": chunk, "metadata": doc["metadata"]})
    
    print(f"Created {len(chunks)} text chunks")
    
    embedding_model = setup_embeddings(model="models/text-embedding-004")
    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    vector_store = Chroma.from_texts(
        texts=texts,
        embedding=embedding_model,
        metadatas=metadatas,
        persist_directory="data/chroma_db",
        collection_name="strength_training_books"
    )
    print("Chroma DB created with collection name: strength_training_books")

if __name__ == "__main__":
    main()