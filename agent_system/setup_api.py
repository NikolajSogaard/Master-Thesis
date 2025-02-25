from dotenv import load_dotenv
import os
import google.generativeai as genai
#from google.generativeai.generative_models import GenerationConfig #Deprecated


def setup_llm(
        model: str,
        max_tokens: int | None = None,
        temperature: float = 0.6,
        top_p: float = 0.9,
        respond_as_json: bool = True,
):
    load_dotenv('cre.env')
    api_key = os.environ.get("GOOGLE_GEMINI_API_KEY")

    if not api_key:
        raise EnvironmentError("GOOGLE_GEMINI_API_KEY is missing.")

    genai.configure(api_key=api_key)

    generation_config = {
        "temperature": temperature,
        "top_p": top_p,
        "max_output_tokens": max_tokens
    }

    model = genai.GenerativeModel(model_name=model)

    def generate_response(prompt):
        response = model.generate_content(prompt, generation_config=generation_config)
        return response.text

    return generate_response