# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-08-23 17:52
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0005_auto_20180824_0048'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='auditlog',
            name='session',
        ),
        migrations.DeleteModel(
            name='SessionTrack',
        ),
    ]
