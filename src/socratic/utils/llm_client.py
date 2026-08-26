## The LLM client for interacting with langauge models

from typing import Any

from openai import OpenAI

from socratic.config import settings

## Client for interacting with LLM providers.
class LLMClient:

    ## This function initializes the LLM client
    def __init__(self):
        self.client = OpenAI(
            base_url=settings.get_llm_base_url(),
            api_key=settings.get_api_key() or "not-needed",
        )
        self.model_name = settings.model_name

    ## This function generates text using the LLM.
    ## It takes in the users prompt, the system prompt which is what makes the LLM not tweak out, the sampling temperature, the maximum amount of tokens that are to be used and any additional arguments. 
    ## The function then returns the generated text response
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs: Any,
    ) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

        return response.choices[0].message.content or ""

    ## This function generates the embeddings for the text
    ## It takes the text to embed for the input and outputs the embedding vector as the output.
    def embed(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            model=settings.embedding_model, input=text
        )
        return response.data[0].embedding


## Global client instance
llm_client = LLMClient()
