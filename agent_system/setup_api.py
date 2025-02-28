from dotenv import load_dotenv
import os
import google.generativeai as genai
import json
import time
from langchain_community.embeddings import GoogleGenerativeAIEmbeddings

# Load environment variables from cre.env
load_dotenv('cre.env')

# Get your credentials from the environment variables
credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
api_key = os.environ.get("GOOGLE_GEMINI_API_KEY")

# Check if both credentials are available
if not credentials_path or not api_key:
    raise EnvironmentError("Required environment variables are missing.")

print("Sensitive credentials loaded successfully!")

# Configure the Gemini API using your API key
genai.configure(api_key=api_key)

def setup_llm(
        model: str,
        max_tokens: int | None = None,
        temperature: float = 0.6,
        top_p: float = 0.9,
        respond_as_json: bool = True,
):
    generation_config = {
        "temperature": temperature,
        "top_p": top_p,
        "max_output_tokens": max_tokens
    }

    gemini_model = genai.GenerativeModel(model_name=model)

    def generate_response(prompt):
        response = gemini_model.generate_content(prompt, generation_config=generation_config)
        if respond_as_json:
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                print("Failed to decode JSON, returning raw text.")
                return response.text
        return response.text

    return generate_response

def setup_embeddings(model="models/text-embedding-004"):
    """
    Set up and return a Google Generative AI embeddings model.
    """
    load_dotenv('cre.env')
    api_key = os.environ.get("GOOGLE_GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("Google API Key is missing.")
    genai.configure(api_key=api_key)

    print(f"Setting up embedding model: {model}")

    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            embedding_model = GoogleGenerativeAIEmbeddings(model=model)
            test_result = embedding_model.embed_query("test")
            if test_result and len(test_result) > 0:
                print(f"Embedding model initialized successfully: {model}")
                return embedding_model
        except Exception as e:
            print(f"Attempt {attempt+1}/{max_retries} failed: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2

    raise ValueError(f"Failed to initialize embedding model after {max_retries} attempts")