from typing import Any

import httpx

from app.integrations.exceptions import IntegrationRequestError, IntegrationResponseError


class BaseApiClient:
    """Shared async HTTP plumbing for outbound integration clients."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 10.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url,
            headers={"X-API-Key": api_key},
            timeout=timeout,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> BaseApiClient:
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = await self._client.request(method, path, **kwargs)
        except httpx.RequestError as exc:
            raise IntegrationRequestError(f"{method} {path} failed: {exc}") from exc

        if response.is_error:
            raise IntegrationResponseError(
                f"{method} {path} returned {response.status_code}: {response.text}",
                status_code=response.status_code,
            )
        return response
