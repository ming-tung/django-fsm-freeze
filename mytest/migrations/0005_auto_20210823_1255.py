# Generated by Django 3.2.6 on 2021-08-23 12:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mytest', '0004_subfakemodel_subsubfakemodel'),
    ]

    operations = [
        migrations.CreateModel(
            name='NonFSMModel',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.AddField(
            model_name='subfakemodel',
            name='another_model',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, to='mytest.nonfsmmodel'),
        ),
    ]
