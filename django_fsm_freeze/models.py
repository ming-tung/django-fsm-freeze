from collections import defaultdict

from dirtyfields import DirtyFieldsMixin
from django.core.exceptions import ValidationError


class FreezeValidationError(ValidationError):
    pass


class FreezableFSMModelMixin(DirtyFieldsMixin):
    class Meta:
        abstract = True

    FROZEN_IN_STATES = ()
    NON_FROZEN_FIELDS = ('state',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_check()

    def freeze_check(self) -> None:
        errors = defaultdict(list)
        if self.state in self.FROZEN_IN_STATES:
            dirty_fields = self.get_dirty_fields(check_relationship=True)
            for field in set(dirty_fields) - set(self.NON_FROZEN_FIELDS):
                errors[field].append(
                    f'The "{field}" field is frozen, but attempting to change it from'
                    f' {dirty_fields[field]} to {getattr(self, field)} ({self!r})'
                )
        if errors:
            raise FreezeValidationError(errors)

    def config_check(self) -> None:
        errors = defaultdict(list)
        for field in self.NON_FROZEN_FIELDS:
            if not hasattr(self, field):
                errors[field].append(f'"{field}" field does not exist.')
        if errors:
            raise FreezeValidationError(errors)

    def save(self, *args, **kwargs) -> None:
        """
        Data freeze checking before saving the object, except when 'update_fields' kwarg
        is passed in. Meaning, one can use 'update_fields' to bypass freeze check.
        """

        # updated_fields is to bypass checking
        if 'update_fields' not in kwargs:
            if kwargs.get('force_insert', None):
                # e.g. object creation
                pass
            else:
                self.freeze_check()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.state in self.FROZEN_IN_STATES:
            raise FreezeValidationError(
                f'{self!r} is frozen, cannot be deleted.'
            )
        return super().delete(*args, **kwargs)
