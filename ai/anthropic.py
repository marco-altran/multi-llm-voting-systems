from ai import AIProcessor
import os
import anthropic
import asyncio


class AnthropicProcessor(AIProcessor):
    def __init__(self, model: str):
        self.client = anthropic.Anthropic(
            api_key=os.environ.get("ANTHROPIC_API_KEY"),
        )
        self.model = model

    def get_vendor(self) -> str:
        return "anthropic"

    def get_model_name(self) -> str:
        return self.model

    def process(self, text_prompt: str, image: bytes) -> str:
        message = self.client.messages.create(
            model=self.model,
            max_tokens=8092,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": text_prompt
                }
            ],
        )
        return message.content[0].text.strip()

    async def process_async(self, text_prompt: str, image: bytes) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.process, text_prompt, image)
