import os
from abc import ABC, abstractmethod

import ollama
from dotenv import load_dotenv

load_dotenv()


class LLMProvider(ABC):
    @abstractmethod
    def complete(self, messages: list[dict], temperature: float = 0) -> str:
        pass


class OllamaProvider(LLMProvider):
    def __init__(self):
        self._client = ollama
        self._model = os.getenv("OLLAMA_MODEL", "llama3.2")

    def complete(self, messages: list[dict], temperature: float = 0) -> str:
        response = self._client.chat(
            model=self._model,
            messages=messages,
            options={"temperature": temperature},
        )
        return response.message.content


class OpenAIProvider(LLMProvider):
    def __init__(self):
        from openai import OpenAI
        self._client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._model = os.getenv("OPENAI_MODEL", "gpt-4o")

    def complete(self, messages: list[dict], temperature: float = 0) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content


def get_provider() -> LLMProvider:
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    if provider == "openai":
        return OpenAIProvider()
    return OllamaProvider()
