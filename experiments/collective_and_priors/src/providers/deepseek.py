"""Compatibility export for the unchanged OpenAI-compatible DeepSeek path."""

from ..agent import OpenAIModelClient

DeepSeekModelClient = OpenAIModelClient

__all__ = ["DeepSeekModelClient"]
