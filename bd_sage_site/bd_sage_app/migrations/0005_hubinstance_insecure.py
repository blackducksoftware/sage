# Generated by Django 2.2.7 on 2019-12-03 12:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bd_sage_app', '0004_auto_20191203_0002'),
    ]

    operations = [
        migrations.AddField(
            model_name='hubinstance',
            name='insecure',
            field=models.BooleanField(default=True),
        ),
    ]
