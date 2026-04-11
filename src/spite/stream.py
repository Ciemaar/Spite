import asyncio
from collections.abc import AsyncGenerator


class ProgressStream:
    """Manages the stream of progress messages."""

    def __init__(self):
        """Initialize the queue for progress messages."""
        self.queue: asyncio.Queue[str | None] = asyncio.Queue()

    async def add_message(self, message: str):
        """Add a message to the stream."""
        await self.queue.put(message)

    async def close(self):
        """Signal the end of the stream."""
        await self.queue.put(None)

    async def get_stream(self) -> AsyncGenerator[str, None]:
        """Generate SSE events from the queue."""
        while True:
            message = await self.queue.get()
            if message is None:
                break
            yield f"event: message\ndata: {message}\n\n"
