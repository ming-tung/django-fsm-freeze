from django.core.exceptions import ValidationError


class FreezeValidationError(ValidationError):
    """Data and field validation-related error."""

    pass


class FreezeConfigurationError(ValidationError):
    """Configuration-related error."""

    pass
