# Generated by Django 5.1.2 on 2024-11-20 08:25

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hoteldetails', '0003_customer'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customer',
            name='room_released',
        ),
        migrations.AddField(
            model_name='customer',
            name='hotel',
            field=models.ForeignKey(default=59, on_delete=django.db.models.deletion.CASCADE, related_name='customers', to='hoteldetails.hoteldetails'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='customer',
            name='room_no',
            field=models.PositiveIntegerField(default=59),
            preserve_default=False,
        ),
    ]