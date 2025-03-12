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

def retrieve_context(query, k=5, min_relevance_score=0, max_context_length=1500):
    """
    Retrieves the top k relevant chunks from the vector store for the query.
    Returns both the context and the source metadata.
    """
    # Initial retrieval - get more than we need for reranking
    initial_k = min(k * 2, 20)  # Retrieve more documents for reranking
    results = vector_store.similarity_search(query, k=initial_k)
    
    # Apply reranking to improve relevance
    reranked_results = rerank_documents(query, results, top_k=k)
    
    # Extract key parts from each document that most directly answer the query
    filtered_content = []
    for res in reranked_results:
        # Extract the most relevant sentences (simple approach)
        sentences = re.split(r'(?<=[.!?])\s+', res.page_content)
        key_sentences = []
        query_keywords = set(re.findall(r'\b\w+\b', query.lower()))
        
        # Keep only sentences with keyword matches or important training terms
        for sentence in sentences[:10]:  # Limit to first 10 sentences per doc
            sentence_lower = sentence.lower()
            # Check for keyword overlap or important training terms
            if (any(keyword in sentence_lower for keyword in query_keywords) or
                any(term in sentence_lower for term in ['training', 'exercise', 'progression', 'intensity', 'volume', 'rpe'])):
                key_sentences.append(sentence)
        
        # Add only relevant content
        if key_sentences:
            source_name = os.path.basename(res.metadata.get('source', 'unknown'))
            filtered_content.append(f"From {source_name}: {' '.join(key_sentences[:5])}")  # Limit to 5 most relevant sentences
    
    # Join all parts with appropriate separators
    context = "\n\n".join(filtered_content)
    
    # Ensure we don't exceed maximum context length
    if len(context) > max_context_length:
        context = context[:max_context_length] + "\n[Content truncated for conciseness]"
    
    # Extract metadata from results for display
    sources = []
    for res in reranked_results:
        sources.append({
            'content': res.page_content[:1000] + "...",  # Show first 100 chars
            'metadata': res.metadata
        })
    
    return context, sources

def retrieve_and_generate(query):
    """
    Combines retrieval and generation:
      1. Retrieves context from the vector store.
      2. Generates and returns an answer using the retrieved information.
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
    
    prompt = f"""You are a specialized strength training expert.
Using the following excerpts from strength training books and programs, provide concise guidance.
{source_summary}

Context:
{context}

Query: {query}

Answer:"""
    return generate_response(prompt), sources
