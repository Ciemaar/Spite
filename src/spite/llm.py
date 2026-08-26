import logging

import dspy  # type: ignore

logger = logging.getLogger(__name__)


def configure_dspy(host: str, model: str) -> None:
    """Configure DSPy with the specified Ollama model globally."""
    dspy_model_name = f"ollama_chat/{model}"
    try:
        lm = dspy.LM(dspy_model_name, api_base=host)
        dspy.settings.configure(lm=lm)
        logger.info(f"Configured DSPy with LM {dspy_model_name} at {host}")
    except Exception as e:
        logger.error(f"Failed to configure DSPy LM: {e}")
        raise
