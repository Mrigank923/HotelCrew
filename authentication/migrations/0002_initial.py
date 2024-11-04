# Generated by Django 5.1.2 on 2024-11-04 08:41

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('authentication', '0001_initial'),
        ('hoteldetails', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='manager',
            name='hotel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='hoteldetails.hoteldetails'),
        ),
        migrations.AddField(
            model_name='manager',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='manager_profile', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='receptionist',
            name='admin',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receptionists', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='receptionist',
            name='hotel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receptionists', to='hoteldetails.hoteldetails'),
        ),
        migrations.AddField(
            model_name='receptionist',
            name='manager',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receptionists', to='authentication.manager'),
        ),
        migrations.AddField(
            model_name='staff',
            name='admin',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='staff', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='staff',
            name='hotel',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='staff', to='hoteldetails.hoteldetails'),
        ),
        migrations.AddField(
            model_name='staff',
            name='manager',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='staff', to='authentication.manager'),
        ),
        migrations.AddField(
            model_name='token',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='auth_token', to=settings.AUTH_USER_MODEL),
        ),
    ]
