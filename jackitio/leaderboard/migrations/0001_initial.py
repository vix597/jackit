# -*- coding: utf-8 -*-
# Generated by Django 1.10.3 on 2016-12-19 00:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Leaderboard',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.CharField(default='', max_length=10)),
                ('score', models.IntegerField()),
                ('points', models.IntegerField()),
                ('playtime', models.IntegerField()),
                ('deaths', models.IntegerField()),
            ],
        ),
    ]