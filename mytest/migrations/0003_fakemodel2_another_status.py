# Generated by Django 3.2.6 on 2021-08-19 07:14

from django.db import migrations
import django_fsm


class Migration(migrations.Migration):

    dependencies = [
        ('mytest', '0002_fakemodel2'),
    ]

    operations = [
        migrations.AddField(
            model_name='fakemodel2',
            name='another_status',
            field=django_fsm.FSMField(default='new', max_length=50),
        ),
    ]
