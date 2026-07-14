from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

import config
import os

# Model name and temperature come from config.py (.env), not hardcoded here.
# Only the Ollama model is used by the graph; instantiate just what we need.
ollama_text_model = ChatOllama(model=config.LLM_MODEL_NAME, temperature=config.LLM_TEMPERATURE)
openai_text_model = ChatOpenAI(model=config.OPENAI_MODEL_NAME, temperature=config.LLM_TEMPERATURE, openai_api_key=config.OPENAI_API_KEY, base_url=config.OPENAI_BASE_URL)

def get_text_model():
    """
    Return the appropriate text model based on the MODEL_PROVIDER environment variable.
    """
    if config.MODEL_PROVIDER == "openai":
        return openai_text_model
    else:
        return ollama_text_model