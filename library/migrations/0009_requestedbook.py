# Generated by Django 3.0.5 on 2022-05-03 10:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0008_auto_20200412_1408'),
    ]

    operations = [
        migrations.CreateModel(
            name='RequestedBook',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enrollment', models.CharField(max_length=40)),
                ('isbn', models.PositiveIntegerField()),
            ],
        ),
    ]
