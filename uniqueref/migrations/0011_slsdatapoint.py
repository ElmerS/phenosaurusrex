# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-05-15 11:51
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('uniqueref', '0010_auto_20161215_1444'),
    ]

    operations = [
        migrations.CreateModel(
            name='SLSDatapoint',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('replicate', models.IntegerField()),
                ('sense', models.IntegerField()),
                ('antisense', models.IntegerField()),
                ('senseratio', models.IntegerField()),
                ('insertions', models.IntegerField()),
                ('binom_fdr', models.IntegerField()),
                ('fcpv_control_1', models.IntegerField()),
                ('fcpv_control_2', models.IntegerField()),
                ('fcpv_control_3', models.FloatField()),
                ('fcpv_control_4', models.FloatField()),
                ('relgene', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='uniqueref.Gene')),
                ('relscreen', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='uniqueref.Screen')),
            ],
            options={
                'verbose_name': 'Datapoint of a Synthetic Lethal selection screen',
                'verbose_name_plural': 'datapoints of synthetic lethal screens',
            },
        ),
    ]