# test_rag.py
from rag_retrieval import retrieve_and_generate, vector_store

def test_retrieve_and_generate():
    # List of sample queries targeting different aspects of strength training.
    queries = [
        "What are the optimal RPE ranges for hypertrophy, for specific exercises?"
    ]
    
    # You can provide any additional instructions for specialized guidance.
    specialized_instruction = (
        "Provide consise guidance, and do not answer outside the scope of the query."
    )
    
    # Print information about the vector store to debug
    try:
        collection_name = vector_store._collection.name
        collection_count = vector_store._collection.count()
        print(f"Vector store collection: {collection_name}")
        print(f"Number of documents in collection: {collection_count}")
    except Exception as e:
        print(f"Error accessing vector store: {e}")
    
    for query in queries:
        print("========================================")
        print("Original Query:", query)
        
        # Directly retrieve context and generate an answer using the RAG pipeline
        answer, sources = retrieve_and_generate(query, specialized_instruction)
        
        # Display the sources that were used
        print(f"\nSources Retrieved: {len(sources)}")
        if not sources:
            print("No sources were found!")
        else:
            for i, source in enumerate(sources, 1):
                print(f"\nSource {i}:")
                if 'metadata' not in source or not source['metadata']:
                    print("  No metadata available")
                else:
                    metadata = source['metadata']
                    for key, value in metadata.items():
                        print(f"  {key}: {value}")
                print(f"  Excerpt: {source['content']}")
            
        print("\nAnswer:")
        print(answer)
        print("========================================\n")

if __name__ == "__main__":
    test_retrieve_and_generate()
