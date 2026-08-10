import requests
import logging

logger = logging.getLogger(__name__)


class LLMExplainer:
    """
    Uses a local LLM (via Ollama) to generate RAG explanations
    for why a specific file is relevant to an issue.
    """

    def __init__(self, model: str = "llama3", ollama_url: str = "http://localhost:11434/api/generate"):
        self.model = model
        self.ollama_url = ollama_url

    def generate_explanation(self, issue_text: str, file_path: str, code_snippet: str) -> str:
        code_block = "```python\n" + code_snippet + "\n```"

        prompt = (
            "You are an expert software engineer.\n"
            "A developer submitted this GitHub issue: \"" + issue_text + "\"\n\n"
            "Our system identified this file as highly relevant: " + file_path + "\n\n"
            "Here is a snippet of the code from that file:\n" + code_block + "\n\n"
            "Explain in 2-3 concise sentences WHY this file is relevant to fixing the issue. "
            "Be direct and technical. Do not hallucinate."
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(self.ollama_url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json().get("response", "No explanation generated.")
        except Exception as e:
            logger.warning("Ollama request failed: " + str(e))
            return "This file is structurally and semantically related to the issue. (Install Ollama and run 'ollama run llama3' for AI explanations)."