import os
import ollama
from ollama import Client

class OllamaService:
    def __init__(self, host=None, model=None):
        self.host = host or os.getenv('OLLAMA_HOST')
        self.model = model or os.getenv('OLLAMA_MODEL', 'mistral')
        self.client = Client(host=self.host) if self.host else None

    def chat(self, messages, options=None):
        if self.client:
            return self.client.chat(model=self.model, messages=messages, options=options or {})
        return ollama.chat(model=self.model, messages=messages, options=options or {})

    def chat_stream(self, messages, options=None):
        if self.client:
            return self.client.chat(model=self.model, messages=messages, options=options or {}, stream=True)
        return ollama.chat(model=self.model, messages=messages, options=options or {}, stream=True)

    def generate(self, prompt, options=None):
        if self.client:
            return self.client.generate(model=self.model, prompt=prompt, options=options or {})
        return ollama.generate(model=self.model, prompt=prompt, options=options or {})
