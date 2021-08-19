from collections import defaultdict
from contextlib import contextmanager
from typing import Optional, Union

from dirtyfields import DirtyFieldsMixin
from django.core.exceptions import FieldDoesNotExist, ValidationError
from django.db import models
from django.db.models.signals import class_prepared
from django.dispatch import receiver
from django_fsm import FSMField


class FreezeValidationError(ValidationError):
    pass


@contextmanager
def bypass_fsm_freeze(objs: Union[object, list]):
    if isinstance(objs, list):
        pass
    else:
        objs = [objs]
    for obj in objs:
        if not isinstance(obj, FreezableFSMModelMixin):
            raise FreezeValidationError(
                f'Unsupported argument {obj!r}. '
                f'`bypass_fsm_freeze()` accepts instance(s) from '
                f'FreezableFSMModelMixin.'
            )
    for obj in objs:
        obj._bypass_fsm_freeze = True
    yield
    for obj in objs:
        obj._bypass_fsm_freeze = False


class FreezableFSMModelMixin(DirtyFieldsMixin, models.Model):
    class Meta:
        abstract = True

    FROZEN_IN_STATES: tuple = ()
    NON_FROZEN_FIELDS: tuple = ()
    FROZEN_STATE_LOOKUP_FIELD: Optional[str]

    _bypass_fsm_freeze: bool = False

    def is_fsm_frozen(self) -> bool:
        """
        Tells, wether or not, condition to apply frozen policy should be
        applied.
        """
        fsm_field = self.__class__._get_fsm_field()
        return fsm_field.value_from_object(self) in self.FROZEN_IN_STATES

    def freeze_check(self) -> None:
        errors = defaultdict(list)
        fsm_field = self.__class__._get_fsm_field()
        if self.is_fsm_frozen():
            dirty_fields = self.get_dirty_fields(check_relationship=True)
            for field in set(dirty_fields) - set(
                self.NON_FROZEN_FIELDS + (fsm_field.name,)
            ):
                errors[field].append('Cannot change frozen field.')
        if errors:
            raise FreezeValidationError(errors)

    @classmethod
    def _get_fsm_field(cls) -> models.Field:
        """
        Autodiscover the FSMField. If multiples are found, then we rely on
        the FSM_STATE_FIELD_NAME property to select it.
        """
        fsm_fields = [
            field for field in cls._meta.fields if isinstance(field, FSMField)
        ]
        if not fsm_fields:
            raise FieldDoesNotExist
        if len(fsm_fields) == 1:
            # Autodetected
            return fsm_fields[0]
        if not hasattr(cls, 'FROZEN_STATE_LOOKUP_FIELD'):
            raise TypeError(
                'Ambiguity to find the frozen state lookup field.'
                ' Please define FROZEN_STATE_LOOKUP_FIELD property'
                f' on the class {cls!r}'
            )
        for field in fsm_fields:
            if field.name == cls.FROZEN_STATE_LOOKUP_FIELD:
                return field
        raise FieldDoesNotExist

    @classmethod
    def config_check(cls) -> None:
        errors = defaultdict(list)
        try:
            cls._get_fsm_field()
        except FieldDoesNotExist:
            errors['FROZEN_STATE_LOOKUP_FIELD'].append('FSMField not found.')

        for field in cls.NON_FROZEN_FIELDS:
            try:
                cls._meta.get_field(field)
            except FieldDoesNotExist:
                errors[field].append(f'{field!r} field does not exist.')
        if errors:
            raise FreezeValidationError(errors)

    def save(self, *args, **kwargs) -> None:
        """Data freeze checking before saving the object."""

        if not self._bypass_fsm_freeze:
            if kwargs.get('force_insert', None):
                # e.g. object creation
                pass
            else:
                self.freeze_check()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if not self._bypass_fsm_freeze and self.is_fsm_frozen():
            raise FreezeValidationError(
                f'{self!r} is frozen, cannot be deleted.'
            )
        return super().delete(*args, **kwargs)


@receiver(class_prepared)
def on_class_prepared(sender, **kwargs):
    if issubclass(sender, FreezableFSMModelMixin):
        sender.config_check()
