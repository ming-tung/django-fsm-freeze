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

## Usage

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

class MyDjangoFSMModel(FreezableFSMModelMixin, models.Model):

    # In this example, when object is in the 'active' state, it is immutable.
    FROZEN_IN_STATES = ('active', )

    NON_FROZEN_FIELDS = FreezableFSMModelMixin.NON_FROZEN_FIELDS + (
        'a_mutable_field',
    )
    # This field is mutable even when the object is in the frozen state.
    a_mutable_field = models.BooleanField()

    # django-fsm specifics: state, transitions, etc.
    state = FSMField(default='new')
    # ...

```

See example usage also in https://github.com/ming-tung/django-fsm-freeze/blob/main/mytest/models.py
