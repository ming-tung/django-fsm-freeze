# django fsm data immutability support
![CI](https://github.com/ming-tung/django-fsm-freeze/actions/workflows/continues-integration.yml/badge.svg?branch=main)
[![PyPI version](https://badge.fury.io/py/django-fsm-freeze.svg)](https://badge.fury.io/py/django-fsm-freeze)
[![Downloads](https://static.pepy.tech/personalized-badge/django-fsm-freeze?period=total&units=international_system&left_color=grey&right_color=yellowgreen&left_text=Downloads)](https://pepy.tech/project/django-fsm-freeze)
[![Coverage Status](https://coveralls.io/repos/github/ming-tung/django-fsm-freeze/badge.svg?branch=main)](https://coveralls.io/github/ming-tung/django-fsm-freeze?branch=main)

django-fsm-freeze provides a django model mixin for data immutability based on
[django-fsm](https://github.com/viewflow/django-fsm).


## Installation

```commandline
pip install django-fsm-freeze
```

## Configuration

- Add `FreezableFSMModelMixin` to your [django-fsm](https://github.com/viewflow/django-fsm) model
- Specify the `FROZEN_IN_STATES` in which the object should be frozen, meaning the
  value of its fields/attributes cannot be changed.
- (optional) Customize the `NON_FROZEN_FIELDS` for mutability

When an object is in a frozen state, by default all of its fields are immutable,
except for the `state` FSMField which needs to be mutable for
[django-fsm](https://github.com/viewflow/django-fsm) to work.
This can be customized via the `FROZEN_STATE_LOOKUP_FIELD` attribute which defaults to 'state'.

In case we still want to mutate certain fields when the object is frozen, we can override
the `NON_FROZEN_FIELDS` to allow it.

```python
from django.db import models
from django_fsm import FSMField

from django_fsm_freeze.models import FreezableFSMModelMixin

class MyDjangoFSMModel(FreezableFSMModelMixin):

    # In this example, when object is in the 'active' state, it is immutable.
    FROZEN_IN_STATES = ('active', )

    NON_FROZEN_FIELDS = ('a_mutable_field', )

    # Assign this with the name of the `FSMField` if your models has multiple FSMFields.
    # See example in `mytest/models.py:FakeModel2`
    FROZEN_STATE_LOOKUP_FIELD = 'state'

    # This field is mutable even when the object is in the frozen state.
    a_mutable_field = models.BooleanField()

    # django-fsm specifics: state, transitions, etc.
    # if another name than `state` is chosen, then you need to customize FSM_STATE_FIELD_NAME
    state = FSMField(default='new')
    # ...

```

See configuration example in https://github.com/ming-tung/django-fsm-freeze/blob/main/mytest/models.py

## Usage

The frozen check takes place when
 - class is prepared (configuration checking)
 - `object.save()`
 - `object.delete()`

In case of trying to save/delete a frozen object, a `FreezeValidationError` will be raised.

If you want to bypass the frozen check for some reason, you can use the contextmanager
`bypass_fsm_freeze()` given the freezable object(s). Then django-fsm-freeze won't do the
checking on `.save()` and `.delete()`.
You can find some usage example in test `mytest/test_models.py:TestBypassFreezeCheck`.

## Developing
For contributors or developers of the project, please see [DEVELOPING.md](docs/DEVELOPING.md)

## Contributing 
(TODO)
For anyone who is interested in contributing to this project, please see [CONTRIBUTING.md](docs/CONTRIBUTING.md).
Thank you :)

For further discussions or suggestions, you could also reach out to me on twitter or email.
