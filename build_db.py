import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from agent_system.setup_api_old import setup_embeddings
from pypdf import PdfReader


def main():
    path = "data/books"
    documents = []
    for filename in os.listdir(path):
        if filename.endswith(".pdf"):
            file_path = os.path.join(path, filename)
            pdf = PdfReader(file_path)
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            documents.append({"text": text, "metadata": {"source": filename}})
    
    if not documents:
        print("No documents found in data/books folder.")
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
    vector_store = Chroma.from_texts(
        texts=texts,
        embedding=embedding_model,
        metadatas=metadatas,
        persist_directory="Data/chroma_db"
    )
    print("Chroma DB created")

if __name__ == "__main__":
    main()

