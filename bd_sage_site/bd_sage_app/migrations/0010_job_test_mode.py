# Generated by Django 2.2.7 on 2019-12-13 16:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bd_sage_app', '0009_auto_20191206_1555'),
    ]

    operations = [
        migrations.AddField(
            model_name='job',
            name='test_mode',
            field=models.BooleanField(default=True, help_text='If enabled, the job will only do a test run. Enabled by default beacuse many of the jobs delete data.'),
        ),
    ]
