from dotenv import load_dotenv
import os
import google.generativeai as genai
import json

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
            # Handle potential JSON formatting issues
            try:
                # Try to clean up the response if it has markdown code blocks
                if response_text.startswith("```json"):
                    response_text = response_text.split("```json", 1)[1]
                if response_text.endswith("```"):
                    response_text = response_text.rsplit("```", 1)[0]
                    
                response_text = response_text.strip()
                return json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"Failed to decode JSON: {e}")
                print(f"Raw text: {response_text}")
                # Return a structured error that can be handled
                return {"error": "JSON parsing error", "raw_text": response_text}
        return response_text  # Return text by default

    return generate_response