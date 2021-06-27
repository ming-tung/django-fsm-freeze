from enum import Enum

from django.db import models
from django_fsm import FSMField, transition

from django_fsm_freeze.models import FreezableFSMModelMixin


class FakeStates(Enum):
    NEW = 'new'
    ACTIVE = 'active'
    ARCHIVED = 'archived'


class FakeModel(FreezableFSMModelMixin, models.Model):
    class Meta:
        abstract = False

    FROZEN_IN_STATES = (
        FakeStates.ACTIVE.value,
        FakeStates.ARCHIVED.value,
    )
    NON_FROZEN_FIELDS = FreezableFSMModelMixin.NON_FROZEN_FIELDS + (
        'can_change_me',
    )

    state = FSMField(default=FakeStates.NEW.value)

    cannot_change_me = models.BooleanField(default=False)
    can_change_me = models.BooleanField(default=False)

    @transition(
        field=state,
        source=FakeStates.NEW.value,
        target=FakeStates.ACTIVE.value,
    )
    def activate(self, *args, **kwargs) -> None:
        pass

    @transition(
        field=state,
        source=FakeStates.ACTIVE.value,
        target=FakeStates.ARCHIVED.value,
    )
    def archive(self, *args, **kwargs) -> None:
        pass
