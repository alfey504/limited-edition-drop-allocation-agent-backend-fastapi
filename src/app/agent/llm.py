from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import Settings

# Tried in order after settings.gemini_model itself fails (rate limit, quota, or any
# other error) — see ModelFallbackMiddleware.
FALLBACK_MODEL_NAMES = [
    "gemini-3.5-flash-lite",
    "gemini-2.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3-flash",
]


def get_llm(settings: Settings) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        api_key=settings.gemini_api_key,
        temperature=0,
    )


def get_fallback_llms(settings: Settings) -> list[ChatGoogleGenerativeAI]:
    return [
        ChatGoogleGenerativeAI(model=model_name, api_key=settings.gemini_api_key, temperature=0)
        for model_name in FALLBACK_MODEL_NAMES
    ]
