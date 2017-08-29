# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-06-27 08:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('uniqueref', '0013_auto_20170515_1529'),
    ]

    operations = [
        migrations.CreateModel(
            name='Settings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('variable_name', models.CharField(max_length=50)),
                ('value', models.TextField()),
                ('comment', models.TextField()),
            ],
            options={
                'verbose_name': 'Manual setting entry',
                'verbose_name_plural': 'Settings for Phenosaurus',
            },
        ),
    ]