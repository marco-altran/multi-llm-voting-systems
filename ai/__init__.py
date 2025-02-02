from abc import ABC, abstractmethod
from langsmith import traceable
from functools import wraps

def trace_llm(run_name: str):
    def decorator(func):
        @wraps(func)
        @traceable(run_name=run_name, project_name="voting-system")
        async def wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                raise
        return wrapper
    return decorator


class AIProcessor(ABC):
    @abstractmethod
    def process(self, text_prompt: str, image: bytes) -> str:
        pass

    @abstractmethod
    @trace_llm("llm_process")
    async def process_async(self, text_prompt: str, image: bytes) -> str:
        pass

    @abstractmethod
    def get_vendor(self) -> str:
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        pass
