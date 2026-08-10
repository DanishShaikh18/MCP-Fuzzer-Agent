"""
Central LLM provider factory.

Every model the agent can use lives here, and only here. To switch which
LLM powers the fuzzer, change LLM_PROVIDER in .env — no other file needs
to change, no code needs to be touched.

Usage in agent.py:
    from src.llm_provider import get_llm
    llm = get_llm()                  # reads LLM_PROVIDER from .env
    llm_with_tools = llm.bind_tools(tools)   # unchanged from before

Supported providers out of the box: gemini, groq, ollama, openai
Add a new one by adding a branch in PROVIDER_BUILDERS below - nothing
else in the codebase needs to know it exists.
"""

import os
from typing import Callable
from langchain_core.language_models.chat_models import BaseChatModel


def _build_gemini(temperature: float) -> BaseChatModel:
    from langchain_google_genai import ChatGoogleGenerativeAI

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("LLM_PROVIDER=gemini but GEMINI_API_KEY is not set in .env")

    return ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        google_api_key=api_key,
        temperature=temperature,
    )


def _build_groq(temperature: float) -> BaseChatModel:
    from langchain_groq import ChatGroq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("LLM_PROVIDER=groq but GROQ_API_KEY is not set in .env")

    return ChatGroq(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        api_key=api_key,
        temperature=temperature,
    )


def _build_ollama(temperature: float) -> BaseChatModel:
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=os.getenv("OLLAMA_MODEL", "llama3.1"),
        base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        temperature=temperature,
    )


def _build_openai(temperature: float) -> BaseChatModel:
    from langchain_openai import ChatOpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("LLM_PROVIDER=openai but OPENAI_API_KEY is not set in .env")

    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=api_key,
        temperature=temperature,
    )


# Registry: add a new provider by adding one line here + one _build_* function above.
PROVIDER_BUILDERS: dict[str, Callable[[float], BaseChatModel]] = {
    "gemini": _build_gemini,
    "groq": _build_groq,
    "ollama": _build_ollama,
    "openai": _build_openai,
}


def get_llm(temperature: float = 0.7, provider: str | None = None) -> BaseChatModel:
    """
    Build and return the configured chat model.

    provider: optional explicit override. If omitted, reads LLM_PROVIDER
    from the environment (falls back to "gemini" if unset).
    """
    selected = (provider or os.getenv("LLM_PROVIDER", "gemini")).strip().lower()

    builder = PROVIDER_BUILDERS.get(selected)
    if builder is None:
        supported = ", ".join(PROVIDER_BUILDERS.keys())
        raise ValueError(
            f"Unknown LLM_PROVIDER '{selected}'. Supported providers: {supported}"
        )

    llm = builder(temperature)
    print(f"[llm_provider] Using provider='{selected}' -> {llm.__class__.__name__}")
    return llm