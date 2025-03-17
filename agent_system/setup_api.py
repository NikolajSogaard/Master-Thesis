from dotenv import load_dotenv
import os
import google.generativeai as genai
import json
from langchain_google_genai import GoogleGenerativeAIEmbeddings

def setup_llm(
        model: str,
        max_tokens: int | None = None,
        temperature: float = 0.6,
        top_p: float = 0.9,
        respond_as_json: bool = False,
):
    # Load environment variables from cre.env
    load_dotenv('cre.env')  # adjust the path if needed

    # Get your credentials from the environment variables
    credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    api_key = os.environ.get("GOOGLE_GEMINI_API_KEY")

    # Check if both credentials are available
    if not credentials_path or not api_key:
        raise EnvironmentError("Required environment variables are missing.")


    # Configure the Gemini API using your API key
    genai.configure(api_key=api_key)

    generation_config = {
        "temperature": temperature,
        "top_p": top_p,
        "max_output_tokens": max_tokens
    }

    gemini_model = genai.GenerativeModel(model_name=model)

    def generate_response(prompt):
        response = gemini_model.generate_content(prompt, generation_config=generation_config)
        response_text = response.text.strip()
        
        if respond_as_json:
            # Attempt to parse JSON if expected, with fallback on failure
            try:
                if response_text.startswith("```json"):
                    response_text = response_text.split("```json", 1)[1]
                if response_text.endswith("```"):
                    response_text = response_text.rsplit("```", 1)[0]
                response_text = response_text.strip()
                return json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"Failed to decode JSON: {e}")
                print(f"Raw text: {response_text}")
                # Fallback: return raw text instead
                return response_text
        return response_text

    return generate_response

def setup_embeddings(model="models/text-embedding-004"):
    """
    Set up and return a Google Generative AI embeddings model.
    
    Args:
        model: The embedding model to use (must use format "models/embedding-001")
    
    Returns:
        A configured embedding model
    """
    # Load environment variables if not already loaded
    load_dotenv('cre.env')  # adjust the path if needed
    
    # Get API key from environment variables
    api_key = os.environ.get("GOOGLE_GEMINI_API_KEY")
    
    # Check if API key is available
    if not api_key:
        raise EnvironmentError("Google API Key is missing.")
    
    # Configure Gemini API if not already configured
    genai.configure(api_key=api_key)
    
    print(f"Setting up embedding model: {model}")
    
    # Initialize with retry mechanism
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            embedding_model = GoogleGenerativeAIEmbeddings(model=model)
            
            # Test the model with a simple embedding
            test_result = embedding_model.embed_query("test")
            if test_result and len(test_result) > 0:
                print(f"Embedding model initialized successfully: {model}")
                return embedding_model
        except Exception as e:
            print(f"Attempt {attempt+1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
    
    raise ValueError(f"Failed to initialize embedding model after {max_retries} attempts")
