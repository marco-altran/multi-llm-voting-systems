import os
import base64
from ai import AIProcessor
from openai import OpenAI


class OpenAIProcessor(AIProcessor):
    def __init__(self, model: str):
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.vendor = "openai"
        self.max_output_tokens = 1000
        self.temperature = 0

    def get_vendor(self) -> str:
        return self.vendor

    def get_model_name(self) -> str:
        return self.model

    def process(self, text_prompt: str, image: bytes) -> str:
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": text_prompt},
                ]
            }
        ]

        if image:
            # Convert the image bytes to a base64-encoded data URL
            image_base64 = base64.b64encode(image).decode(
                'utf-8') if isinstance(image, bytes) else image
            if not image_base64.startswith('data:'):
                image_type = "image/jpeg" if image_base64.startswith(
                    "/9j/") else "image/png"
                image_base64 = f"data:{image_type};base64,{image_base64}"

            messages[0]["content"].append(
                {"type": "image_url", "image_url": {"url": image_base64}})

        response = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_output_tokens,
            messages=messages
        )
        return response.choices[0].message.content.strip()
