import logging
from typing import Any

import dspy  # type: ignore
from ollama import AsyncClient, Message

logger = logging.getLogger(__name__)


class LLMInterface:
    """Unified interface to interact with language models."""

    def __init__(self, host: str, model: str):
        """Initialize the LLM interface with host and model selection."""
        self.host = host
        self.model = model
        self.client = AsyncClient(host=host)

        # Initialize DSPy LM. DSPy v2 uses dspy.LM with LiteLLM provider format
        # ollama models are prefixed with "ollama_chat/" or "ollama/"
        dspy_model_name = f"ollama_chat/{self.model}"
        try:
            self.dspy_lm = dspy.LM(dspy_model_name, api_base=self.host)
            dspy.settings.configure(lm=self.dspy_lm)
            logger.info(f"Configured DSPy with LM {dspy_model_name} at {self.host}")
        except Exception as e:
            logger.error(f"Failed to configure DSPy LM: {e}")
            self.dspy_lm = None

    async def generate_response(self, system_prompt: str, user_prompt: str) -> str:
        """Generate a text response from the LLM."""
        messages: list[Message] = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_prompt),
        ]

        try:
            logger.info(f"Calling Ollama model {self.model} at {self.host}")
            response: Any = await self.client.chat(model=self.model, messages=messages)  # pyright: ignore
            return response["message"]["content"]  # type: ignore
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            raise
