import os
import base64
from openai import NOT_GIVEN, OpenAI
from openai import AsyncOpenAI

from ai import AIProcessor


class OpenAIProcessor(AIProcessor):
    def __init__(self, model: str):
        self.model = model
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.async_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.vendor = "openai"
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
            reasoning_effort="high" if self.model.startswith("o") else NOT_GIVEN,
            messages=messages
        )
        return response.choices[0].message.content.strip()

    async def process_async(self, text_prompt: str, image: bytes) -> str:
        messages = self._build_messages(text_prompt, image)

        response = await self.async_client.chat.completions.create(
            model=self.model,
            reasoning_effort="high" if self.model.startswith("o") else NOT_GIVEN,
            messages=messages
        )
        return response.choices[0].message.content.strip()

    async def classify_letter_async(self, prompt: str, answer: str, image: bytes) -> str:
        """Classify the answer as one of A, B, C, D, or E using structured output."""
        base_messages = self._build_messages(prompt, image) + self._build_messages(answer, image)
        messages = [
            {"role": "system", "content": "Classify the answer in JSON format as one of the multiple choice options."}
        ] + base_messages
        
        response = await self.async_client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format={"type": "json_object"},
            functions=[{
                "name": "classify_answer",
                "description": "Classify the answer in JSON format as one of the multiple choice options",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "answer": {
                            "type": "string",
                            "description": "The answer letter (A, B, C, D, E, etc)"
                        }
                    },
                    "required": ["answer"]
                }
            }],
            function_call={"name": "classify_answer"}
        )
        
        function_call = response.choices[0].message.function_call
        if function_call and function_call.arguments:
            import json
            result = json.loads(function_call.arguments)
            return result["answer"]
        return response.choices[0].message.content.strip()
