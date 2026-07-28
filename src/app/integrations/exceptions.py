class IntegrationError(Exception):
    """Raised when a call to an external service fails."""


class IntegrationRequestError(IntegrationError):
    """The request could not be completed (network failure, timeout, DNS)."""


class IntegrationResponseError(IntegrationError):
    """The external service responded with a non-2xx status."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code
