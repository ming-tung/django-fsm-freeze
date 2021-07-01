from collections import defaultdict

from dirtyfields import DirtyFieldsMixin
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db.models.signals import class_prepared
from django.dispatch import receiver


class FreezeValidationError(ValidationError):
    pass


class FreezableFSMModelMixin(DirtyFieldsMixin):
    class Meta:
        abstract = True

    FROZEN_IN_STATES = ()
    NON_FROZEN_FIELDS = ('state',)

    def freeze_check(self) -> None:
        errors = defaultdict(list)
        if self.state in self.FROZEN_IN_STATES:
            dirty_fields = self.get_dirty_fields(check_relationship=True)
            for field in set(dirty_fields) - set(self.NON_FROZEN_FIELDS):
                errors[field].append('Cannot change frozen field.')
        if errors:
            raise FreezeValidationError(errors)

    @classmethod
    def config_check(cls) -> None:
        errors = defaultdict(list)
        for field in cls.NON_FROZEN_FIELDS:
            try:
                cls._meta.get_field(field)
            except FieldDoesNotExist:
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


@receiver(class_prepared)
def on_class_prepared(sender, **kwargs):
    if issubclass(sender, FreezableFSMModelMixin):
        sender.config_check()
