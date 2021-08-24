import threading
from collections import defaultdict
from contextlib import contextmanager
from typing import Any, Iterable, Optional, Union

from dirtyfields import DirtyFieldsMixin
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models.signals import class_prepared
from django.dispatch import receiver
from django_fsm import FSMField

from django_fsm_freeze.exceptions import (
    FreezeConfigurationError,
    FreezeValidationError,
)

_DISABLED_FSM_FREEZE = threading.local()


@contextmanager
def bypass_fsm_freeze(
    objs: Union[
        'FreezableFSMModelMixin', Iterable['FreezableFSMModelMixin']
    ] = (),
    bypass_globally: bool = False,
):
    """
    Bypass the frozen checks.

    objs: the object(s) that will not be checked for its frozeness
    bypass_globally: flag to apply the bypassing globally
    """

    if objs and not isinstance(objs, Iterable):
        objs = (objs,)
    errors = []
    for obj in objs:
        if not isinstance(obj, FreezableFSMModelMixin):
            errors.append(
                f'Unsupported argument(s): {obj!r}. '
                f'`bypass_fsm_freeze()` accepts instance(s) from '
                f'FreezableFSMModelMixin.'
            )
    if errors:
        raise FreezeConfigurationError(errors)

    try:
        if bypass_globally is True:
            _DISABLED_FSM_FREEZE.active = True
        for obj in objs:
            obj._bypass_fsm_freeze = True
        yield
    finally:
        if bypass_globally is True:
            _DISABLED_FSM_FREEZE.active = False
        for obj in objs:
            obj._bypass_fsm_freeze = False


def resolve_dotted_path(instance: Any, path: str) -> Any:
    """
    Walk recursively the path separated by dots.
    """
    for part in path.split('.'):
        instance = getattr(instance, part)
    return instance


class FreezableFSMModelMixin(DirtyFieldsMixin, models.Model):
    """
    Support for django-fsm data immutability.

    FROZEN_IN_STATES: fsm states that an instance is considered frozen in
    FROZEN_STATE_LOOKUP_FIELD: the field used to be looked up for the state
    FROZEN_DELEGATE_TO: the field used to be looked up for the state (via
                        foreignkey, dot-separated path).
                        Cannot be combined with `FROZEN_STATE_LOOKUP_FIELD`.
    NON_FROZEN_FIELDS: fields that are mutable
    """

    class Meta:
        abstract = True

    FROZEN_IN_STATES: tuple = ()
    FROZEN_STATE_LOOKUP_FIELD: Optional[str]
    FROZEN_DELEGATE_TO: Optional[str] = None
    NON_FROZEN_FIELDS: tuple = ()

    _bypass_fsm_freeze: bool = False

    @property
    def is_fsm_frozen(self) -> bool:
        """Determine whether self is frozen or not."""

        instance, fsm_field = self._resolve_delegation()
        return (
            fsm_field.value_from_object(instance) in instance.FROZEN_IN_STATES
        )

    def _resolve_delegation(self) -> tuple['FreezableFSMModelMixin', FSMField]:
        """
        Find the FreezableFSMModelMixin instance and its FSMState field
        """

        if self.FROZEN_DELEGATE_TO:
            instance = resolve_dotted_path(self, self.FROZEN_DELEGATE_TO)
            if not isinstance(instance, FreezableFSMModelMixin):
                raise FreezeConfigurationError(
                    {
                        'FROZEN_DELEGATE_TO': [
                            'Does not resolve to a'
                            ' FreezableFSMModelMixin model.'
                        ]
                    }
                )
            return instance, instance.__class__._get_fsm_field()
        return self, self.__class__._get_fsm_field()

    @property
    def _is_fsm_freeze_bypassed(self) -> bool:
        return bool(
            getattr(_DISABLED_FSM_FREEZE, 'active', False)
            or self._bypass_fsm_freeze
        )

    def freeze_check(self) -> None:
        """Check dirty fields and frozen status.

        Raise `FreezeValidationError` if it is dirty and frozen.
        """

        if self._is_fsm_freeze_bypassed or not self.is_fsm_frozen:
            return
        errors = defaultdict(list)
        instance, fsm_field = self._resolve_delegation()
        dirty_fields = self.get_dirty_fields(check_relationship=True)
        for field in set(dirty_fields) - set(
            instance.NON_FROZEN_FIELDS + (fsm_field.name,)
        ):
            errors[field].append('Cannot change frozen field.')
        if errors:
            raise FreezeValidationError(errors)

    @classmethod
    def _get_fsm_field(cls) -> FSMField:
        """Discover the FSMField.

        If multiples are found, we use FROZEN_STATE_LOOKUP_FIELD to select it.
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
                ' Please define FROZEN_STATE_LOOKUP_FIELD attribute'
                f' on the class {cls!r}'
            )
        for field in fsm_fields:
            if field.name == cls.FROZEN_STATE_LOOKUP_FIELD:
                return field
        raise FieldDoesNotExist

    @classmethod
    def config_check(cls) -> None:
        errors = defaultdict(list)
        if cls.FROZEN_DELEGATE_TO:
            if cls.FROZEN_IN_STATES:
                errors['FROZEN_IN_STATES'].append(
                    'Field FROZEN_DELEGATE_TO is already defined.'
                )
            if getattr(cls, 'FROZEN_STATE_LOOKUP_FIELD', None):
                errors['FROZEN_STATE_LOOKUP_FIELD'].append(
                    'Field FROZEN_DELEGATE_TO is already defined.'
                )
        else:
            try:
                cls._get_fsm_field()
            except FieldDoesNotExist:
                errors['FROZEN_STATE_LOOKUP_FIELD'].append(
                    'FSMField not found.'
                )
            except TypeError as err:
                errors['FROZEN_STATE_LOOKUP_FIELD'].append(str(err))

        for field in cls.NON_FROZEN_FIELDS:
            try:
                cls._meta.get_field(field)
            except FieldDoesNotExist:
                errors[field].append(f'{field!r} field does not exist.')
        if errors:
            raise FreezeConfigurationError(errors)

    def save(self, *args, **kwargs) -> None:
        """Data freeze checking before saving the object."""

        if not kwargs.get('force_insert', None):
            # e.g. not object creation
            self.freeze_check()

        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if not self._is_fsm_freeze_bypassed and self.is_fsm_frozen:
            raise FreezeValidationError(
                f'{self!r} is frozen, cannot be deleted.'
            )
        return super().delete(*args, **kwargs)


@receiver(class_prepared)
def on_class_prepared(sender, **kwargs):
    if issubclass(sender, FreezableFSMModelMixin):
        sender.config_check()
