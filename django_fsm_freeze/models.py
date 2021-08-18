from collections import defaultdict

from dirtyfields import DirtyFieldsMixin
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import models
from django.db.models.signals import class_prepared
from django.dispatch import receiver
from django_fsm import FSMField


class FreezeValidationError(ValidationError):
    pass


class FreezableFSMModelMixin(DirtyFieldsMixin, models.Model):
    class Meta:
        abstract = True

    FROZEN_IN_STATES: tuple = ()
    FSM_STATE_FIELD_NAME: str = 'state'
    NON_FROZEN_FIELDS: tuple = (FSM_STATE_FIELD_NAME,)

    def freeze_check(self) -> None:
        errors = defaultdict(list)
        if getattr(self, self.FSM_STATE_FIELD_NAME) in self.FROZEN_IN_STATES:
            dirty_fields = self.get_dirty_fields(check_relationship=True)
            for field in set(dirty_fields) - set(self.NON_FROZEN_FIELDS):
                errors[field].append('Cannot change frozen field.')
        if errors:
            raise FreezeValidationError(errors)

    @classmethod
    def config_check(cls) -> None:
        errors = defaultdict(list)
        try:
            fsm_state_field = cls._meta.get_field(cls.FSM_STATE_FIELD_NAME)
        except FieldDoesNotExist:
            errors['FSM_STATE_FIELD_NAME'].append(
                f'{cls.FSM_STATE_FIELD_NAME!r} field does not exist.'
            )
        else:
            if not isinstance(fsm_state_field, FSMField):
                errors['FSM_STATE_FIELD_NAME'].append(
                    f'{cls.FSM_STATE_FIELD_NAME!r} must be an FSMField.'
                )

        for field in cls.NON_FROZEN_FIELDS:
            try:
                cls._meta.get_field(field)
            except FieldDoesNotExist:
                errors[field].append(f'{field!r} field does not exist.')
        if errors:
            raise FreezeValidationError(errors)

    def save(self, *args, **kwargs) -> None:
        """Data freeze checking before saving the object.

        Note: checking is skipped when 'update_fields' kwarg is passed in.
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
        if getattr(self, self.FSM_STATE_FIELD_NAME) in self.FROZEN_IN_STATES:
            raise FreezeValidationError(
                f'{self!r} is frozen, cannot be deleted.'
            )
        return super().delete(*args, **kwargs)


@receiver(class_prepared)
def on_class_prepared(sender, **kwargs):
    if issubclass(sender, FreezableFSMModelMixin):
        sender.config_check()
