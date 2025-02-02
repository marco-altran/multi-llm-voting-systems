import os
import base64
from openai import OpenAI
from openai import AsyncOpenAI

from ai import AIProcessor


class OpenRouterProcessor(AIProcessor):
    def __init__(self, model: str):
        self.model = model
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        self.async_client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            timeout=60.0  # Increased timeout for potentially slower responses
        )
        self.vendor = "openrouter"
        self.max_output_tokens = 8092
        self.temperature = 0

    def _build_messages(self, text_prompt: str, image: bytes) -> list:
        # Build the base message with the text prompt
        messages = [
            {
                "role": "user",
                "content": text_prompt
            }
        ]
        return messages

    def get_vendor(self) -> str:
        return self.vendor

    def get_model_name(self) -> str:
        return self.model

    def process(self, text_prompt: str, image: bytes) -> str:
        messages = self._build_messages(text_prompt, image)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        return response.choices[0].message.content.strip()

    async def process_async(self, text_prompt: str, image: bytes) -> str:
        messages = self._build_messages(text_prompt, image)

        response = await self.async_client.chat.completions.create(
            model=self.model,
            messages=messages
        )
        return response.choices[0].message.content.strip()
