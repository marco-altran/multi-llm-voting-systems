from abc import ABC, abstractmethod


class AIProcessor(ABC):
    @abstractmethod
    def process(self, text_prompt: str, image: bytes) -> str:
        pass

    @abstractmethod
    async def process_async(self, text_prompt: str, image: bytes) -> str:
        pass

    @abstractmethod
    def get_vendor(self) -> str:
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        pass
