from langchain_ollama import ChatOllama

import config

# Model name and temperature come from config.py (.env), not hardcoded here.
# Only the Ollama model is used by the graph; instantiate just what we need.
ollama_text_model = ChatOllama(model=config.LLM_MODEL_NAME, temperature=config.LLM_TEMPERATURE)
