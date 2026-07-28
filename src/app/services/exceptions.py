class ServiceError(Exception):
    """Base error for business-rule violations raised from the service layer."""


class EmailAlreadyRegisteredError(ServiceError):
    pass


class InvalidCredentialsError(ServiceError):
    pass


class ConversationNotFoundError(ServiceError):
    pass


class ConversationAccessDeniedError(ServiceError):
    pass
