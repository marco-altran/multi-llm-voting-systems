from ai import AIProcessor
import os
import anthropic
import base64


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
            max_tokens=1000,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64.b64encode(image).decode('utf-8')
                            }
                        },
                        {
                            "type": "text",
                            "text": text_prompt
                        }
                    ] if image else [
                        {
                            "type": "text",
                            "text": text_prompt
                        }
                    ]
                }
            ],
        )
        return message.content[0].text.strip()
