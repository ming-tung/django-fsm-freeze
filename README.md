# django fsm data immutability support
![CI](https://github.com/ming-tung/django-fsm-freeze/actions/workflows/continues-integration.yml/badge.svg?branch=main)
[![PyPI version](https://badge.fury.io/py/django-fsm-freeze.svg)](https://badge.fury.io/py/django-fsm-freeze)
[![Downloads](https://static.pepy.tech/personalized-badge/django-fsm-freeze?period=total&units=international_system&left_color=grey&right_color=yellowgreen&left_text=Downloads)](https://pepy.tech/project/django-fsm-freeze)

django-fsm-freeze provides a django model mixin for data immutability based on
[django-fsm](https://github.com/viewflow/django-fsm).


## Installation

```commandline
pip install django-fsm-freeze
```

## Configuration

### Basic configuration
- Add `FreezableFSMModelMixin` to your [django-fsm](https://github.com/viewflow/django-fsm) model
- Specify the `FROZEN_IN_STATES` in which the object should be frozen, meaning the
  value of its fields/attributes cannot be changed.
- (optional) Customize the `NON_FROZEN_FIELDS` for partial mutability

When an object is in a frozen state, by default all of its fields are immutable,
except for the `state` FSMField which needs to be mutable for
[django-fsm](https://github.com/viewflow/django-fsm) to work.

```python
from django_fsm import FSMField

from django_fsm_freeze.models import FreezableFSMModelMixin

class MyDjangoFSMModel(FreezableFSMModelMixin):

    # In this example, when object is in the 'active' state, it is immutable.
    FROZEN_IN_STATES = ('active', )
    
    # django-fsm specifics: state, transitions, etc.
    state = FSMField(default='new')
    # ...
```

### Customization

#### Tell django-fsm-freeze which field to look up for frozeness
By default, FreezableFSMModelMixin will look for the FSMField on your model
and its value to determine whether the instance is frozen or not.
However, in case your model has multiple `FSMField`s,
you would need to tell the Mixin which field should be used to look up,
to determine the frozeness via the `FROZEN_STATE_LOOKUP_FIELD` attribute.

```python
from django.db import models
from django_fsm import FSMField

from django_fsm_freeze.models import FreezableFSMModelMixin

class MyDjangoFSMModel(FreezableFSMModelMixin):

    # In this example, when object is in the 'active' state, it is immutable.
    FROZEN_IN_STATES = ('active', )

    # Assign this with the name of the `FSMField` if your models has multiple FSMFields.
    # See example in `mytest/models.py:FakeModel2`
    FROZEN_STATE_LOOKUP_FIELD = 'state'
    
    # django-fsm specifics: state, transitions, etc.
    state = FSMField(default='new')
    another_state = FSMField(default='draft')
    # ...
```

In another case, when the desired lookup state is on another model related
via foreign key, instead of setting `FROZEN_STATE_LOOKUP_FIELD`,
it is possible to specify the (dot-separated) path to that field in
`FROZEN_DELEGATE_TO`.
This setting instructs the freezable model instance to evaluate the freezable
state from that remote field.

```python
class Parent(FreezableFSMModelMixin):
    state = FSMField(default='new')


class Child(FreezableFSMModelMixin):

    # Assign this with the path (dotted separated) to the instance you expect
    # the decision for freezability to be decided on.
    FROZEN_DELEGATE_TO = 'parent'
    parent = models.ForeignKey(Parent, on_delete=models.PROTECT)
```

#### Define for partial mutability 
In case we want to mutate certain fields when the object is frozen, we can
set the `NON_FROZEN_FIELDS` to allow it.

```python
class MyDjangoFSMModel(FreezableFSMModelMixin):

    # In this example, when object is in the 'active' state, it is immutable.
    FROZEN_IN_STATES = ('active', )
    NON_FROZEN_FIELDS = ('a_mutable_field', )

    # This field is mutable even when the object is in the frozen state.
    a_mutable_field = models.BooleanField()
```
See configuration example in https://github.com/ming-tung/django-fsm-freeze/blob/main/mytest/models.py

## Usage

The frozen check takes place when
 - class is prepared (configuration checking)
 - `object.save()`
 - `object.delete()`

In case of trying to save/delete a frozen object, a `FreezeValidationError` will be raised.
In case of misconfiguration, a `FreezeConfigurationError` will be raised.


### Bypassing
If you want to bypass the frozen check for some reason, you can use the contextmanager
`bypass_fsm_freeze()`, with the freezable object(s) that you want to bypass
the checks on, or apply the bypass globally via `bypass_globally` argument.

You can find some usage example in test `mytest/test_models.py:TestBypassFreezeCheck`.

## Developing
For contributors or developers of the project, please see [DEVELOPING.md](docs/DEVELOPING.md)

## Contributing 
(TODO)
For anyone who is interested in contributing to this project, please see [CONTRIBUTING.md](docs/CONTRIBUTING.md).
Thank you :)

For further discussions or suggestions, you could also reach out to me on twitter or email.
