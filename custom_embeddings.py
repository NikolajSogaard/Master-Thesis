from langchain.embeddings.base import Embeddings
import google.generativeai as genai
from typing import List

class CustomGoogleEmbeddings(Embeddings):
    """Custom implementation of Google's text embeddings using generative-ai API."""
    
    def __init__(self, model: str = "models/text-embedding-004"):
        self.model = model
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents using Google's API"""
        results = []
        for text in texts:
            embedding = self.embed_query(text)
            results.append(embedding)
        return results
    
    def embed_query(self, text: str) -> List[float]:
        """Embed a query using Google's API"""
        result = genai.embed_content(
            model=self.model,
            content=text,
            task_type="retrieval_document"
        )
        return result["embedding"]
