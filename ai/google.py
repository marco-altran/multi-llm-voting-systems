import os

import google.generativeai as genai
import vertexai
from vertexai.generative_models import GenerativeModel, Part, FinishReason
import vertexai.preview.generative_models as generative_models
from ai import AIProcessor


class GoogleProcessor(AIProcessor):
    def __init__(self, model: str):
        self.model = model
        # vertexai.init(project=os.environ.get("VERTEX_AI_PROJECT_ID"),
        #               location=os.environ.get("VERTEX_AI_LOCATION"))
        genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel(self.model)
        self.max_output_tokens = 1000
        self.temperature = 0
        self.vendor = "google"

    def get_vendor(self) -> str:
        return self.vendor

    def get_model_name(self) -> str:
        return self.model._model_name.split("/")[-1]

    def process(self, text_prompt: str, image: bytes) -> str:
        generation_config = {
            "max_output_tokens": self.max_output_tokens,
            "temperature": self.temperature,
        }

        safety_settings = {
            generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_ONLY_HIGH,
        }

        # image_type = "image/jpeg" if image[:
        #                                    23] == b"data:image/jpeg;base64," else "image/png"
        # video1 = Part.from_data(
        #     mime_type=image_type,
        #     data=image,
        # )

        responses = self.model.generate_content(
            text_prompt,
            generation_config=generation_config,
            stream=True,
        )

        result = ""
        for response in responses:
            result += response.text
        return result.strip()
