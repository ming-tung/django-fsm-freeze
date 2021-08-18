from enum import Enum

from django.db import models
from django_fsm import FSMField, transition

from django_fsm_freeze.models import FreezableFSMModelMixin


class FakeStates(Enum):
    NEW = 'new'
    ACTIVE = 'active'
    ARCHIVED = 'archived'


class FakeModel(FreezableFSMModelMixin):

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


class FakeModel2(FreezableFSMModelMixin):

    FROZEN_IN_STATES = (
        FakeStates.ACTIVE.value,
        FakeStates.ARCHIVED.value,
    )
    FSM_STATE_FIELD_NAME = 'status'
    NON_FROZEN_FIELDS = (FSM_STATE_FIELD_NAME, 'can_change_me')

    status = FSMField(default=FakeStates.NEW.value)

    cannot_change_me = models.BooleanField(default=False)
    can_change_me = models.BooleanField(default=False)

    @transition(
        field=status,
        source=FakeStates.NEW.value,
        target=FakeStates.ACTIVE.value,
    )
    def activate(self, *args, **kwargs) -> None:
        pass

    @transition(
        field=status,
        source=FakeStates.ACTIVE.value,
        target=FakeStates.ARCHIVED.value,
    )
    def archive(self, *args, **kwargs) -> None:
        pass
