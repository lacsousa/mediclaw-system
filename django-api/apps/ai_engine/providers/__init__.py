import os


def get_provider():
    name = os.environ.get("LLM_PROVIDER", "openai").lower()
    if name == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider()
    if name == "gemini":
        from .gemini_provider import GeminiProvider

        return GeminiProvider()
    raise RuntimeError(f"Unknown LLM_PROVIDER: {name}")
