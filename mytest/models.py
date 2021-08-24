from enum import Enum

from django.db import models
from django_fsm import FSMField, transition

from django_fsm_freeze.models import FreezableFSMModelMixin


class FakeStates(Enum):
    NEW = 'new'
    ACTIVE = 'active'
    ARCHIVED = 'archived'


class NonFSMModel(models.Model):
    pass


class FakeModel(FreezableFSMModelMixin):

    FROZEN_IN_STATES = (
        FakeStates.ACTIVE.value,
        FakeStates.ARCHIVED.value,
    )
    NON_FROZEN_FIELDS = ('can_change_me',)

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


class SubFakeModel(FreezableFSMModelMixin):
    FROZEN_DELEGATE_TO = 'fake_model'
    NON_FROZEN_FIELDS = ('can_change_me',)

    fake_model = models.ForeignKey(FakeModel, on_delete=models.PROTECT)
    another_model = models.ForeignKey(
        NonFSMModel, on_delete=models.SET_DEFAULT, null=True, default=None
    )
    can_change_me = models.BooleanField(default=False)
    cannot_change_me = models.BooleanField(default=False)


class SubSubFakeModel(FreezableFSMModelMixin):
    FROZEN_DELEGATE_TO = 'sub_fake_model.fake_model'
    NON_FROZEN_FIELDS = ('can_change_me',)

    sub_fake_model = models.ForeignKey(SubFakeModel, on_delete=models.PROTECT)
    can_change_me = models.BooleanField(default=False)
    cannot_change_me = models.BooleanField(default=False)


class FakeModel2(FreezableFSMModelMixin):
    """Have two FSMFields, and define one as FROZEN_STATE_LOOKUP_FIELD."""

    FROZEN_IN_STATES = (
        FakeStates.ACTIVE.value,
        FakeStates.ARCHIVED.value,
    )
    FROZEN_STATE_LOOKUP_FIELD = 'status'
    NON_FROZEN_FIELDS = ('can_change_me',)

    status = FSMField(default=FakeStates.NEW.value)
    another_status = FSMField(default=FakeStates.NEW.value)

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
