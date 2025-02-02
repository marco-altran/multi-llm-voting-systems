from ai.anthropic import AnthropicProcessor
from ai.google import GoogleProcessor
from ai.openai import OpenAIProcessor
from ai.openrouter import OpenRouterProcessor
from ai import AIProcessor


def create_ai_processor(provider: str, model: str) -> AIProcessor:
    if provider == "anthropic":
        return AnthropicProcessor(model)
    elif provider == "google":
        return GoogleProcessor(model)
    elif provider == "openai":
        return OpenAIProcessor(model)
    elif provider == "openrouter":
        return OpenRouterProcessor(model)
    else:
        raise ValueError(f"Unknown provider: {provider}")
