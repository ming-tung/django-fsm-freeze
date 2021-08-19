import pytest

from django_fsm_freeze.models import FreezeValidationError
from mytest.models import FakeModel, FakeModel2


@pytest.fixture
def active_fake_obj():
    fake_obj = FakeModel.objects.create()
    fake_obj.activate()
    return fake_obj


@pytest.mark.django_db
class TestFreezableFSMModelMixin:
    def test_fields_are_frozen_when_in_frozen_state(self):
        fake_obj = FakeModel.objects.create()
        fake_obj.activate()
        assert fake_obj.state in FakeModel.FROZEN_IN_STATES

        fake_obj.cannot_change_me = True
        fake_obj.can_change_me = True

        with pytest.raises(FreezeValidationError) as err:
            fake_obj.save()

        assert (
            err.value.message_dict['cannot_change_me'][0]
            == 'Cannot change frozen field.'
        )

    def test_fields_not_frozen_when_in_frozen_state(self, active_fake_obj):
        _original_non_frozen_fields = FakeModel.NON_FROZEN_FIELDS
        FakeModel.NON_FROZEN_FIELDS = ('state', 'cannot_change_me')

        active_fake_obj.cannot_change_me = True
        # no error raised because 'cannot_change_me' is not frozen
        active_fake_obj.save()

        FakeModel.NON_FROZEN_FIELDS = _original_non_frozen_fields

    def test_not_freeze_when_not_in_frozen_state(
        self,
    ):
        fake_obj = FakeModel.objects.create()
        assert fake_obj.state not in FakeModel.FROZEN_IN_STATES

        fake_obj.cannot_change_me = True
        fake_obj.save()  # no error raised

    def test_freeze_works_with_fsm_transitions(
        self,
        active_fake_obj,
    ):
        assert active_fake_obj.state in FakeModel.FROZEN_IN_STATES

        active_fake_obj.archive()  # no error raised

    def test_allow_deletion_in_non_frozen_state(
        self,
    ):
        fake_obj = FakeModel.objects.create()
        assert fake_obj.state not in FakeModel.FROZEN_IN_STATES

        fake_obj.delete()  # no error raised

    def test_dont_allow_deletion_in_frozen_state(self, active_fake_obj):
        assert active_fake_obj.state in FakeModel.FROZEN_IN_STATES

        with pytest.raises(FreezeValidationError) as err:
            active_fake_obj.delete()

        assert (
            err.value.message
            == f'{active_fake_obj!r} is frozen, cannot be deleted.'
        )

    def test_can_call_transition(self, active_fake_obj):
        """By default the state field is editable"""
        active_fake_obj.archive()
        active_fake_obj.save()

    def test_state_name_can_differ(self):
        fake_obj = FakeModel2.objects.create()
        assert fake_obj.status == 'new'

    def test_fsm_state_field_name(self):
        assert FakeModel2._get_fsm_field() is FakeModel2._meta.get_field(
            'status'
        )
        FakeModel2.FSM_STATE_FIELD_NAME = 'not_a_field'
        with pytest.raises(FreezeValidationError) as err:
            FakeModel2.config_check()
        assert err.value == FreezeValidationError(
            {'FSM_STATE_FIELD': 'FSMField not found.'}
        )
