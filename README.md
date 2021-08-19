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

- Add `FreezableFSMModelMixin` to your [django-fsm](https://github.com/viewflow/django-fsm) model
- Specify the `FROZEN_IN_STATES` in which the object should be frozen, meaning the
  value of its fields/attributes cannot be changed.
- (optional) Customize the `NON_FROZEN_FIELDS` for mutability

When an object is in a frozen state, by default all of its fields are immutable,
except for the `state` field which needs to be mutable for
[django-fsm](https://github.com/viewflow/django-fsm) to work.

In case we still want to mutate certain fields when the object is frozen, we can override
the `NON_FROZEN_FIELDS` to allow it.
When overriding the `NON_FROZEN_FIELDS`, be careful to include `state` for the reason
mentioned above.


```python
from django.db import models
from django_fsm import FSMField

from django_fsm_freeze.models import FreezableFSMModelMixin

class MyDjangoFSMModel(FreezableFSMModelMixin):

    # In this example, when object is in the 'active' state, it is immutable.
    FROZEN_IN_STATES = ('active', )

    NON_FROZEN_FIELDS = FreezableFSMModelMixin.NON_FROZEN_FIELDS + (
        'a_mutable_field',
    )

    # Assign this with the name of the`FSMField` if it is not 'state'.
    # If your are using 'state' as the `FSMField` in your model, you can leave this one out.
    # See example in `mytest/models.py:FakeModel2`
    FSM_STATE_FIELD_NAME = 'state'

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

*Note* that in the current design, passing `update_fields` kwarg in `.save()` will bypass the frozen check,
because here we assume it's user's intention to save the specified fields without trouble/raising error.

See usage example in tests https://github.com/ming-tung/django-fsm-freeze/blob/main/mytest/test_models.py

# Development
This is for contributors or developers of the project.
The usual stuff :)

- First, install the package then try to run tests.
  ```bash
  # install dependencies from lock file
  poetry install

  # run checks and tests
  poetry run flake8 .
  poetry run isort .
  poetry run pytest
  ```

- Whether working on a feature or a bug fix, write meaningful test(s) that fail.
- Work on the code change
- Pass the test(s)
- Review your own work
- When you are happy, open a Pull Request and ask for review :)

## Make a Release
For the owner and contributors, when the time comes, we use github Release (and Actions)
to publish the package to PyPI.

- In the Release page, start by "Draft a new release"
- We use semantic versioning and prefix with the letter "v", e.g. "v0.1.7"
- Choose the target branch (usually `main`) and write a meaningful Release title and description
- Click on "Publish release" to trigger the CI to automatically publish the package to PyPI
