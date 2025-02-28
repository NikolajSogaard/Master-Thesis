import os
import sys
from collections import defaultdict
import argparse
from langchain_chroma import Chroma  # Updated import

# Add the project root to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from agent_system.setup_api import setup_embeddings

def inspect_chroma_database(db_path=os.path.join("Data", "chroma_db"), sample_size=2):
    """
    Inspect the Chroma database to verify content from all sources.
    
    Args:
        db_path: Path to the Chroma database
        sample_size: Number of sample chunks to show for each source
    """
    print(f"Loading Chroma database from: {db_path}")
    
    # Setup embedding function
    embedding_model = setup_embeddings(model="models/text-embedding-004")
    
    # Load the database
    db = Chroma(
        persist_directory=db_path,
        embedding_function=embedding_model
    )
    
    # Get all documents in the database
    results = db.get()
    
    if not results or not results.get('metadatas'):
        print("No documents found in the database.")
        return
    
    # Group documents by source
    docs_by_source = defaultdict(list)
    
    for i, metadata in enumerate(results['metadatas']):
        source = metadata.get('source', 'unknown')
        docs_by_source[source].append({
            'id': results['ids'][i] if 'ids' in results else i,
            'text': results['documents'][i] if 'documents' in results else "No content",
            'metadata': metadata
        })
    
    # Extract unique book names (from source paths)
    book_names = set()
    for source in docs_by_source.keys():
        if '/' in source or '\\' in source:
            # Extract just the filename
            filename = os.path.basename(source)
            book_names.add(filename)
    
    # Display summary statistics
    print(f"\nTotal documents in database: {len(results['metadatas'])}")
    print(f"Number of unique sources: {len(docs_by_source)}")
    print(f"Number of unique books: {len(book_names)}")
    print("\nBooks found in the database:")
    for book in sorted(book_names):
        print(f"- {book}")
    
    # Display sample content from each source
    print("\n=== SAMPLE CONTENT BY SOURCE ===")
    for source, documents in sorted(docs_by_source.items()):
        print(f"\n### SOURCE: {source}")
        print(f"Total chunks: {len(documents)}")
        
        # Show sample documents
        for i, doc in enumerate(documents[:sample_size]):
            print(f"\nSample {i+1}:")
            print(f"Text preview: {doc['text'][:150]}...")
        
        if len(documents) > sample_size:
            print(f"...and {len(documents) - sample_size} more chunks")
    
    # Test a query for each book
    print("\n=== TESTING QUERIES BY BOOK ===")
    for book in sorted(book_names):
        book_name_terms = os.path.splitext(book)[0].replace('_', ' ').lower()
        query = f"information about {book_name_terms}"
        
        print(f"\nQuery: '{query}'")
        try:
            results = db.similarity_search_with_score(query, k=1)
            if results:
                doc, score = results[0]
                print(f"Found result with score: {score:.4f}")
                print(f"Source: {doc.metadata.get('source')}")
                print(f"Text: {doc.page_content[:100]}...")
            else:
                print("No results found")
        except Exception as e:
            print(f"Error querying: {str(e)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Inspect Chroma database content")
    parser.add_argument("--db-path", default="chroma_db", help="Path to Chroma database")
    parser.add_argument("--sample-size", type=int, default=1, help="Number of samples per source")
    args = parser.parse_args()
    
    inspect_chroma_database(db_path=args.db_path, sample_size=args.sample_size)
