import logging

import uvicorn


def main() -> None:
    """Run the main spite server."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.info("Starting spite server...")
    uvicorn.run("spite.main:app", host="0.0.0.0", port=8000, reload=True)
