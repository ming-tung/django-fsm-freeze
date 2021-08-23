import pytest

from django_fsm_freeze.exceptions import (
    FreezeConfigurationError,
    FreezeValidationError,
)
from django_fsm_freeze.models import bypass_fsm_freeze
from mytest.models import FakeModel, FakeModel2


@pytest.fixture
def active_fake_obj():
    fake_obj = FakeModel.objects.create()
    fake_obj.activate()
    fake_obj.save()
    return fake_obj


@pytest.fixture
def active_fake2_obj():
    fake_obj = FakeModel2.objects.create()
    fake_obj.activate()
    fake_obj.save()
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
        fake_obj.refresh_from_db()
        assert fake_obj.cannot_change_me is False
        assert fake_obj.can_change_me is False

    def test_fields_not_frozen_when_in_frozen_state(self, active_fake_obj):
        _original_non_frozen_fields = FakeModel.NON_FROZEN_FIELDS
        FakeModel.NON_FROZEN_FIELDS = ('state', 'cannot_change_me')

        active_fake_obj.cannot_change_me = True
        # no error raised because 'cannot_change_me' is not frozen
        active_fake_obj.save()
        active_fake_obj.refresh_from_db()
        assert active_fake_obj.cannot_change_me is True

        FakeModel.NON_FROZEN_FIELDS = _original_non_frozen_fields

    def test_not_freeze_when_not_in_frozen_state(
        self,
    ):
        fake_obj = FakeModel.objects.create()
        assert fake_obj.state not in FakeModel.FROZEN_IN_STATES

        fake_obj.cannot_change_me = True
        fake_obj.save()  # no error raised

        fake_obj.refresh_from_db()
        assert fake_obj.cannot_change_me is True

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

    @pytest.mark.parametrize('mymodel', [FakeModel, FakeModel2])
    def test_can_call_transition(self, mymodel):
        """By default, 'state' FSMField is editable."""

        active_fake_obj = mymodel.objects.create()
        active_fake_obj.activate()
        active_fake_obj.archive()
        active_fake_obj.save()

    def test_state_name_can_differ(self):
        fake_obj = FakeModel2.objects.create()
        assert fake_obj.status == 'new'

    def test_fsm_state_field_name_is_not_a_fsmfield(self):
        assert FakeModel2._get_fsm_field() is FakeModel2._meta.get_field(
            'status'
        )

        previous_value = FakeModel2.FROZEN_STATE_LOOKUP_FIELD
        try:
            FakeModel2.FROZEN_STATE_LOOKUP_FIELD = 'not_a_field'

            with pytest.raises(FreezeConfigurationError) as err:
                FakeModel2.config_check()

            assert err.value == FreezeConfigurationError(
                {'FROZEN_STATE_LOOKUP_FIELD': 'FSMField not found.'}
            )
        finally:
            FakeModel2.FROZEN_STATE_LOOKUP_FIELD = previous_value

    def test_fsm_state_field_name_should_be_specified(self):
        """Require FROZEN_STATE_LOOKUP_FIELD when multiple `FSMField`s found"""

        previous_value = FakeModel2.FROZEN_STATE_LOOKUP_FIELD
        try:
            del FakeModel2.FROZEN_STATE_LOOKUP_FIELD

            with pytest.raises(FreezeConfigurationError) as err:
                FakeModel2.config_check()

            assert err.value == FreezeConfigurationError(
                {
                    'FROZEN_STATE_LOOKUP_FIELD': f'Ambiguity to find the'
                    f' frozen state lookup field. Please define'
                    f' FROZEN_STATE_LOOKUP_FIELD attribute on the class'
                    f' {FakeModel2!r}'
                }
            )
        finally:
            FakeModel2.FROZEN_STATE_LOOKUP_FIELD = previous_value


@pytest.mark.django_db
class TestBypassFreezeCheck:
    def test_bypass_fsm_freeze_empty(self, active_fake_obj):
        active_fake_obj.cannot_change_me = True

        with bypass_fsm_freeze():  # empty input, i.e. globally bypassed
            active_fake_obj.save()

        active_fake_obj.refresh_from_db()
        assert active_fake_obj.cannot_change_me is True

    def test_bypass_fsm_freeze_input_list(self, active_fake_obj):
        active_fake_obj.cannot_change_me = True

        with bypass_fsm_freeze((active_fake_obj,)):
            active_fake_obj.save()  # no error raised

        active_fake_obj.refresh_from_db()
        assert active_fake_obj.cannot_change_me is True

    def test_bypass_fsm_freeze_on_save(self, active_fake_obj):
        active_fake_obj.cannot_change_me = True
        with pytest.raises(FreezeValidationError):
            active_fake_obj.save()

        with bypass_fsm_freeze(active_fake_obj):
            active_fake_obj.save()  # no error raised

        active_fake_obj.refresh_from_db()
        assert active_fake_obj.cannot_change_me is True

    def test_bypass_fsm_freeze_on_delete(self, active_fake_obj):
        with pytest.raises(FreezeValidationError):
            active_fake_obj.delete()

        with bypass_fsm_freeze(active_fake_obj):
            active_fake_obj.delete()  # no error raised

    def test_bypass_fsm_freeze_input_not_a_freezable_obj(self):
        not_a_freezable_obj = object()
        input_objs = [not_a_freezable_obj, 'some-str']

        with pytest.raises(FreezeConfigurationError) as err:
            with bypass_fsm_freeze(input_objs):
                pass

        assert err.value.error_list[0] == FreezeConfigurationError(
            f'Unsupported argument(s): {not_a_freezable_obj!r}. '
            f'`bypass_fsm_freeze()` accepts instance(s) from '
            f'FreezableFSMModelMixin.'
        )
        assert err.value.error_list[1] == FreezeConfigurationError(
            "Unsupported argument(s): 'some-str'. "
            '`bypass_fsm_freeze()` accepts instance(s) from '
            'FreezableFSMModelMixin.'
        )

    def test_bypass_fsm_freeze_globally(
        self, active_fake_obj, active_fake2_obj
    ):
        active_fake_obj.cannot_change_me = True
        active_fake2_obj.cannot_change_me = True

        with bypass_fsm_freeze():
            active_fake_obj.save()
            active_fake2_obj.save()

        active_fake_obj.refresh_from_db()
        active_fake2_obj.refresh_from_db()
        assert active_fake_obj.cannot_change_me is True
        assert active_fake2_obj.cannot_change_me is True

        with bypass_fsm_freeze():
            active_fake_obj.delete()
            active_fake2_obj.delete()

        assert FakeModel.objects.count() == 0

    def test_bypass_input_objs_and_global(
        self, active_fake_obj, active_fake2_obj
    ):
        active_fake_obj.cannot_change_me = True
        active_fake2_obj.cannot_change_me = True

        with pytest.raises(FreezeValidationError):
            with bypass_fsm_freeze(active_fake_obj):
                active_fake_obj.save()
                active_fake2_obj.save()

        active_fake_obj.refresh_from_db()
        active_fake2_obj.refresh_from_db()
        assert active_fake_obj.cannot_change_me is True
        assert active_fake2_obj.cannot_change_me is False

        with pytest.raises(FreezeValidationError):
            with bypass_fsm_freeze(active_fake_obj):
                active_fake_obj.delete()
                active_fake2_obj.delete()

        assert FakeModel.objects.count() == 0
        assert FakeModel2.objects.count() == 1
