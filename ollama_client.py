import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "phi3:mini"  # light model that fits in low RAM

def generate_text_with_ollama(prompt: str) -> str:
    """
    Send a prompt to the local Ollama model and return the full response text.
    """
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_ctx": 512,      # small context window to save memory
            "num_predict": 256   # limit length of response
        }
    }

    response = requests.post(OLLAMA_URL, json=payload)

    if response.status_code != 200:
        print("\n[Ollama ERROR] Status:", response.status_code)
        print(response.text)  # show the server message
        response.raise_for_status()

    data = response.json()
    return data.get("response", "").strip()
