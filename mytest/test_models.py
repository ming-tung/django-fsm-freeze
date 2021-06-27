import pytest

from django_fsm_freeze.models import FreezeValidationError
from mytest.models import FakeModel


@pytest.fixture
def active_fake_obj():
    fake_obj = FakeModel.objects.create()
    fake_obj.activate()
    return fake_obj


@pytest.mark.django_db
class TestFreezableFSMModelMixin:
    def test_non_frozen_fields_configuration_error(self):
        assert not hasattr(FakeModel, 'fake_field')
        _original_non_frozen_fields = FakeModel.NON_FROZEN_FIELDS
        FakeModel.NON_FROZEN_FIELDS = ('fake_field',)

        with pytest.raises(FreezeValidationError) as err:
            _ = FakeModel.objects.create()

        assert (
            err.value.message_dict['fake_field'][0]
            == '"fake_field" field does not exist.'
        )

        FakeModel.NON_FROZEN_FIELDS = _original_non_frozen_fields

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
            == f'The "cannot_change_me" field is frozen, but attempting to change it from'
            f' False to True ({fake_obj!r})'
        )

    def test_fields_not_frozen_when_in_frozen_state(self, active_fake_obj):
        _original_non_frozen_fields = FakeModel.NON_FROZEN_FIELDS
        FakeModel.NON_FROZEN_FIELDS = ('state', 'cannot_change_me')

        active_fake_obj.cannot_change_me = True
        active_fake_obj.save()  # no error raised because 'cannot_change_me' is not frozen

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
