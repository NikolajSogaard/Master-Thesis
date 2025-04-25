import os
import numpy as np
from langchain_chroma import Chroma
from agent_system.setup_api import setup_embeddings, setup_llm


embedding_model = setup_embeddings(model="models/text-embedding-004")
generate_response = setup_llm(model="models/gemini-2.0-flash", max_tokens=10000, temperature=0.3)

vector_store = Chroma(
    persist_directory="data/chroma_db",
    embedding_function=embedding_model,  # Pass the entire embedding_model object, not just the method
    collection_name="strength_training_books"
)

# Helper Functions

def simple_summary(text):
    # Returns a simple summary (first 200 characters)
    return text[:200] + "..." if len(text) > 200 else text

def rerank_results(results):
    # Rerank by sorting results based on the length of page_content (longer first)
    return sorted(results, key=lambda x: len(x.page_content), reverse=True)

# Retrieval Function: Get Context from ChromaDB

def retrieve_context(query, k=8):
    """
    Retrieves the top k relevant chunks from the vector store for the query.
    Returns the prompt context, a simple summary, and the source metadata.
    """
    # Use the original query directly without expansion
    results = vector_store.similarity_search(query, k=k)
    results = rerank_results(results)
    
    # Extract page content for the prompt context
    context = "\n\n".join([res.page_content for res in results])
    
    # Generate a simple summary from the context
    summary = simple_summary(context)
    
    # Extract metadata from results for display
    sources = []
    for res in results:
        sources.append({
            'content': res.page_content[:100] + "...",  # Show first 100 chars
            'metadata': res.metadata
        })
    
    return context, summary, sources


def retrieve_and_generate(query, specialized_instructions=""):
    """
    Combines retrieval and generation:
      1. Retrieves context from the vector store.
      2. Builds a prompt that includes any specialized instructions and a summary.
      3. Generates and returns an answer using Gemini Flash 2.0.
    """
    context, summary, sources = retrieve_context(query)
    prompt = f"""You are a specialized strength training expert.
{specialized_instructions}

Using the following excerpts from strength training books, programs.
Include practical advice recommendations, and clear explanations.
Do not answer outside the scope of the query.

Summary of Retrieved Information:
{summary}

Context:
{context}

Query: {query}

Answer:"""
    return generate_response(prompt), sources
