# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-08-24 07:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0006_auto_20180824_0152'),
    ]

    operations = [
        migrations.AddField(
            model_name='host',
            name='enabled',
            field=models.BooleanField(default=True, help_text='主机若不想被用户访问可以去掉此选项'),
        ),
    ]