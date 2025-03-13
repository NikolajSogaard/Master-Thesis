import os
import numpy as np
from langchain_chroma import Chroma
from agent_system.setup_api import setup_embeddings, setup_llm
import re
from typing import List, Dict, Any, Tuple

embedding_model = setup_embeddings(model="models/text-embedding-004")
generate_response = setup_llm(model="models/gemini-2.0-flash", max_tokens=1000, temperature=0.7)

vector_store = Chroma(
    persist_directory="data/chroma_db",
    embedding_function=embedding_model,  # Pass the entire embedding_model object, not just the method
    collection_name="strength_training_books"
)

def rerank_documents(query: str, results, top_k: int = 10):
    """
    Reranks retrieved documents using a simple relevance scoring mechanism.
    """
    reranked_results = []
    
    # Calculate relevance score based on keyword matching and position
    query_keywords = set(re.findall(r'\b\w+\b', query.lower()))
    
    for doc in results:
        text = doc.page_content.lower()
        
        # Calculate keyword overlap score
        text_words = set(re.findall(r'\b\w+\b', text))
        keyword_overlap = len(query_keywords.intersection(text_words))
        
        # Calculate recency/position score if available in metadata
        position_score = 0
        if hasattr(doc, 'metadata') and 'page' in doc.metadata:
            try:
                # Prefer documents that appear earlier in their sources
                position_score = 1 / (int(doc.metadata['page']) + 1)
            except (ValueError, TypeError):
                pass
                
        # Calculate final score
        relevance_score = keyword_overlap + position_score
        
        reranked_results.append((doc, relevance_score))
    
    # Sort by score in descending order and take top k
    reranked_results.sort(key=lambda x: x[1], reverse=True)  # Changed 'descending' to 'reverse'
    return [item[0] for item in reranked_results[:top_k]]

def retrieve_context(query, k=5, min_relevance_score=0):
    """
    Retrieves the top k relevant chunks from the vector store for the query.
    Returns both the context and the source metadata.
    """
    # Initial retrieval - get more than we need for reranking
    initial_k = min(k * 2, 20)  # Retrieve more documents for reranking
    results = vector_store.similarity_search(query, k=initial_k)
    
    # Apply reranking to improve relevance
    reranked_results = rerank_documents(query, results, top_k=k)
    
    # Group by source for better context organization
    source_grouped = {}
    for res in reranked_results:
        source = res.metadata.get('source', 'unknown')
        if source not in source_grouped:
            source_grouped[source] = []
        source_grouped[source].append(res)
    
    # Build organized context with source headings
    context_parts = []
    for source, docs in source_grouped.items():
        source_name = os.path.basename(source) if isinstance(source, str) else "Unknown Source"
        context_parts.append(f"--- From: {source_name} ---")
        for doc in docs:
            context_parts.append(doc.page_content)
    
    # Join all parts with appropriate separators
    context = "\n\n".join(context_parts)
    
    # Truncate if too long (prevent context overflow)
    max_context_length = 2000  # Adjust based on your model's context window
    if len(context) > max_context_length:
        context = context[:max_context_length] + "\n[Content truncated due to length]"
    
    # Extract metadata from results for display
    sources = []
    for res in reranked_results:
        sources.append({
            'content': res.page_content[:1000] + "...",  # Show first 100 chars
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
    
    # Create source summary for prompt
    source_summary = ""
    if sources:
        unique_sources = set()
        for s in sources:
            if 'source' in s['metadata']:
                source_name = os.path.basename(s['metadata']['source'])
                unique_sources.add(source_name)
        
        if unique_sources:
            source_summary = f"Information retrieved from: {', '.join(unique_sources)}"
    
    # Add specialized instructions only if provided
    instruction_text = ""
    if specialized_instructions and specialized_instructions.strip():
        instruction_text = specialized_instructions + "\n\n"
    
    prompt = f"""You are a specialized strength training expert.
{instruction_text}Using the following excerpts from strength training books and programs, provide concise guidance.
Include practical advice, exercise recommendations, and clear explanations.
{source_summary}

Context:
{context}

Query: {query}

Answer:"""
    return generate_response(prompt), sources
