from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import Settings


def get_llm(settings: Settings) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        api_key=settings.gemini_api_key,
        temperature=0,
    )
