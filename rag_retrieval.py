import os
import numpy as np
from langchain_chroma import Chroma
from agent_system.setup_api import setup_embeddings, setup_llm


embedding_model = setup_embeddings(model="models/text-embedding-004")
generate_response = setup_llm(model="models/gemini-2.0-flash", max_tokens=500, temperature=0.7)

vector_store = Chroma(
    persist_directory="data/chroma_db",
    embedding_function=embedding_model,  # Pass the entire embedding_model object, not just the method
    collection_name="strength_training_books"
)

# Retrieval Function: Get Context from ChromaDB

def retrieve_context(query, k=8):
    """
    Retrieves the top k relevant chunks from the vector store for the query.
    Returns both the context and the source metadata.
    """
    # Use the original query directly without expansion
    results = vector_store.similarity_search(query, k=k)
    
    # Extract page content for the prompt context
    context = "\n\n".join([res.page_content for res in results])
    
    # Extract metadata from results for display
    sources = []
    for res in results:
        sources.append({
            'content': res.page_content[:100] + "...",  # Show first 100 chars
            'metadata': res.metadata
        })
    
    return context, sources


def retrieve_and_generate(query, specialized_instructions=""):
    """
    Combines retrieval and generation:
      1. Retrieves context from the vector store.
      2. Builds a prompt that includes any specialized instructions.
      3. Generates and returns an answer using Gemini Flash 2.0.
    """
    context, sources = retrieve_context(query)
    prompt = f"""You are a specialized strength training expert.
{specialized_instructions}

Using the following excerpts from strength training books, programs, provide consise guidance.
Include practical advice, exercise recommendations, and clear explanations.

Context:
{context}

Query: {query}

Answer:"""
    return generate_response(prompt), sources
