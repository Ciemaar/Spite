import logging
from typing import Any

from ollama import AsyncClient, Message

logger = logging.getLogger(__name__)

class LLMInterface:
    """Unified interface to interact with language models."""

    def __init__(self, host: str, model: str):
        """Initialize the LLM interface with host and model selection."""
        self.host = host
        self.model = model
        self.client = AsyncClient(host=host)

    async def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a text response from the LLM."""
        messages: list[Message] = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_prompt),
        ]

        try:
            logger.info(f"Calling Ollama model {self.model} at {self.host}")
            response: Any = await self.client.chat(model=self.model, messages=messages)  # pyright: ignore
            return response["message"]["content"] # type: ignore
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            raise
