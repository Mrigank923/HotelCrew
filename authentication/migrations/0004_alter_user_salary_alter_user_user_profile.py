# Generated by Django 5.1.2 on 2024-11-18 19:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0003_manager_shift_receptionist_shift_staff_is_avaliable_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='salary',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='user_profile',
            field=models.ImageField(blank=True, default='media/14-cd-campogalliano-web-1565969801.jpg', null=True, upload_to='media/'),
        ),
    ]