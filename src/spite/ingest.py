import base64
import logging
from pathlib import Path
from urllib.parse import urlparse

import httpx
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)

class IngestionManager:
    """Manages the ingestion of source materials for the dirty agent."""

    def __init__(self, github_token: str | None = None):
        """Initialize the ingestion manager with an optional GitHub token."""
        self.github_token = github_token
        self.client = httpx.AsyncClient(timeout=30.0)
        if github_token:
            self.client.headers.update(
                {"Authorization": f"Bearer {github_token}"}
            )

    async def close(self):
        """Close the underlying HTTP client."""
        await self.client.aclose()

    async def ingest_github_repo(self, repo_url: str) -> dict[str, str]:
        """Fetch strictly filtered files from a GitHub repository."""
        parsed = urlparse(repo_url)
        path_parts = [p for p in parsed.path.split("/") if p]
        if len(path_parts) < 2:
            raise ValueError("Invalid GitHub URL")
        owner, repo = path_parts[0], path_parts[1]

        # Strip trailing .git
        if repo.endswith(".git"):
            repo = repo[:-4]

        # Get default branch
        repo_info_url = f"https://api.github.com/repos/{owner}/{repo}"
        repo_resp = await self.client.get(repo_info_url)
        repo_resp.raise_for_status()
        default_branch = repo_resp.json().get("default_branch", "main")

        # Get the tree
        tree_url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/{default_branch}?recursive=1"
        tree_resp = await self.client.get(tree_url)
        tree_resp.raise_for_status()
        tree_data = tree_resp.json()

        files_content: dict[str, str] = {}
        for item in tree_data.get("tree", []):
            if item["type"] == "blob":
                path = item["path"]
                if self._is_allowed_file(path):
                    logger.info(f"Fetching {path} from {owner}/{repo}")
                    content = await self._fetch_blob(owner, repo, item["sha"])
                    if content is not None:
                        files_content[path] = content

        return files_content

    def _is_allowed_file(self, path: str) -> bool:
        """Strictly filter files to only docs and type stubs."""
        allowed_extensions = {".md", ".rst", ".txt", ".html", ".pyi", ".d.ts"}
        p = Path(path)

        if p.name.upper() == "README":
            return True
        if p.suffix.lower() in allowed_extensions or p.name.endswith(".d.ts"):
            return True
        return False

    async def _fetch_blob(self, owner: str, repo: str, sha: str) -> str | None:
        url = f"https://api.github.com/repos/{owner}/{repo}/git/blobs/{sha}"
        resp = await self.client.get(url)
        if resp.status_code == 200:
            data = resp.json()
            if data["encoding"] == "base64":
                try:
                    return base64.b64decode(data["content"]).decode("utf-8")
                except UnicodeDecodeError:
                    return None
        return None

    async def fetch_urls(self, urls: list[str]) -> dict[str, str]:
        """Fetch the text content of a list of URLs."""
        results: dict[str, str] = {}
        for url in urls:
            try:
                resp = await self.client.get(url)
                if resp.status_code == 200:
                    results[url] = resp.text
            except Exception as e:
                logger.warning(f"Failed to fetch {url}: {e}")
        return results

    def search_web(self, query: str) -> str:
        """Perform a web search using DuckDuckGo."""
        try:
            results = DDGS().text(query, max_results=5)
            formatted = "\n\n".join(
                [
                    f"Title: {r['title']}\nLink: {r['href']}\nSnippet: {r['body']}"
                    for r in results
                ]
            )
            return formatted
        except Exception as e:
            logger.warning(f"Web search failed: {e}")
            return ""
