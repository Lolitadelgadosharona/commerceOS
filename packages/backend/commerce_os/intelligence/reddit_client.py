import base64
import json
from dataclasses import dataclass
from typing import Any, Protocol
from urllib import parse, request

from commerce_os.intelligence.errors import IntelligenceValidationError


@dataclass(frozen=True)
class RedditItem:
    external_id: str
    kind: str
    subreddit: str
    title: str
    content: str
    author_reference: str | None
    score: int
    comment_count: int
    published_timestamp: float
    permalink: str


class RedditReadTransport(Protocol):
    def read_posts(self, subreddit: str, time_window: str, limit: int) -> list[RedditItem]: ...

    def read_comments(self, post_id: str, subreddit: str, limit: int) -> list[RedditItem]: ...


class RedditApiClient:
    """OAuth-only Reddit reader. This class intentionally exposes no write operation."""

    token_url = "https://www.reddit.com/api/v1/access_token"
    api_base = "https://oauth.reddit.com"

    def __init__(self, client_id: str, client_secret: str, user_agent: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        self._token: str | None = None
        self.rate_limit_remaining: float | None = None
        self.rate_limit_reset_seconds: float | None = None

    def read_posts(self, subreddit: str, time_window: str, limit: int) -> list[RedditItem]:
        payload = self._get(
            f"/r/{parse.quote(subreddit, safe='')}/top",
            {"t": time_window, "limit": str(limit), "raw_json": "1"},
        )
        return [self._item(child["data"], "post") for child in payload["data"]["children"]]

    def read_comments(self, post_id: str, subreddit: str, limit: int) -> list[RedditItem]:
        payload = self._get(
            f"/r/{parse.quote(subreddit, safe='')}/comments/{parse.quote(post_id, safe='')}",
            {"limit": str(limit), "raw_json": "1", "depth": "1"},
        )
        children = payload[1]["data"]["children"] if len(payload) > 1 else []
        return [
            self._item(child["data"], "comment") for child in children if child.get("kind") == "t1"
        ][:limit]

    def _get(self, path: str, query: dict[str, str]) -> Any:
        if self.rate_limit_remaining is not None and self.rate_limit_remaining <= 0:
            raise IntelligenceValidationError("Reddit rate limit is exhausted; retry after reset.")
        url = f"{self.api_base}{path}?{parse.urlencode(query)}"
        call = request.Request(
            url,
            method="GET",
            headers={
                "Authorization": f"Bearer {self._access_token()}",
                "User-Agent": self.user_agent,
            },
        )
        try:
            with request.urlopen(call, timeout=20) as response:  # noqa: S310
                remaining = response.headers.get("X-Ratelimit-Remaining")
                reset = response.headers.get("X-Ratelimit-Reset")
                self.rate_limit_remaining = float(remaining) if remaining is not None else None
                self.rate_limit_reset_seconds = float(reset) if reset is not None else None
                return json.loads(response.read())
        except Exception as exc:
            raise IntelligenceValidationError("Reddit read request failed.") from exc

    def _access_token(self) -> str:
        if self._token:
            return self._token
        credentials = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        body = parse.urlencode({"grant_type": "client_credentials"}).encode()
        call = request.Request(
            self.token_url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Basic {credentials}",
                "User-Agent": self.user_agent,
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        try:
            with request.urlopen(call, timeout=20) as response:  # noqa: S310
                token = json.loads(response.read()).get("access_token")
        except Exception as exc:
            raise IntelligenceValidationError("Reddit OAuth authentication failed.") from exc
        if not token:
            raise IntelligenceValidationError("Reddit OAuth response did not include a token.")
        self._token = str(token)
        return self._token

    @staticmethod
    def _item(data: dict[str, Any], kind: str) -> RedditItem:
        return RedditItem(
            external_id=str(data["id"]),
            kind=kind,
            subreddit=str(data.get("subreddit", "")),
            title=str(data.get("title", "")),
            content=str(data.get("selftext") or data.get("body") or ""),
            author_reference=(
                str(data["author_fullname"]) if data.get("author_fullname") else None
            ),
            score=int(data.get("score", 0)),
            comment_count=int(data.get("num_comments", 0)),
            published_timestamp=float(data["created_utc"]),
            permalink=str(data.get("permalink", "")),
        )
