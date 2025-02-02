import os
import asyncio
import google.generativeai as genai
from ai import AIProcessor


class GoogleProcessor(AIProcessor):
    def __init__(self, model: str):
        self.model = model
        # vertexai.init(project=os.environ.get("VERTEX_AI_PROJECT_ID"),
        #               location=os.environ.get("VERTEX_AI_LOCATION"))
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(self.model)
        self.vendor = "google"

    def get_vendor(self) -> str:
        return self.vendor

    def get_model_name(self) -> str:
        return self.model._model_name.split("/")[-1]

    def process(self, text_prompt: str, image: bytes) -> str:

        # image_type = "image/jpeg" if image[:
        #                                    23] == b"data:image/jpeg;base64," else "image/png"
        # video1 = Part.from_data(
        #     mime_type=image_type,
        #     data=image,
        # )

        responses = self.model.generate_content(
            text_prompt,
            stream=True,
        )
            
        result = ""
        for response in responses:
            result += response.text
        return result.strip()

    async def process_async(self, text_prompt: str, image: bytes) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.process, text_prompt, image)
