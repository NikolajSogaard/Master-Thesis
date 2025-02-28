import os
import sys

# Add project root to Python path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

# Use absolute import instead of relative import
from agent_system.rag_retriever import RagRetriever

def print_database_stats(retriever):
    """Print statistics about the database"""
    # Get all documents in the database
    all_docs = retriever.db.get()
    print(f"Total documents in database: {len(all_docs['ids'])}")
    
    # Show some document sources if available
    if 'metadatas' in all_docs and all_docs['metadatas']:
        print("\nSample document sources:")
        unique_sources = set()
        for metadata in all_docs['metadatas']:
            if 'source' in metadata:
                unique_sources.add(metadata['source'])
            elif 'filename' in metadata:
                unique_sources.add(metadata['filename'])
        
        for source in list(unique_sources)[:10]:  # Show at most 10 sources
            print(f"- {source}")
        if len(unique_sources) > 10:
            print(f"... and {len(unique_sources) - 10} more")

def test_retriever(query):
    """Test the retriever with a specific query"""
    retriever = RagRetriever()
    
    print(f"\n--- Testing query: '{query}' ---\n")
    
    # Get results using the query_with_context method
    results = retriever.query_with_context(query)
    print(results)
    
    return retriever

if __name__ == "__main__":
    # Test queries to try
    test_queries = [
        "strength training for beginners",
        "recovery techniques after workouts",
        "nutrition for muscle building"
    ]
    
    # Choose one query to test
    retriever = test_retriever(test_queries[0])
    
    # Print database statistics
    print("\n--- Database Statistics ---")
    print_database_stats(retriever)