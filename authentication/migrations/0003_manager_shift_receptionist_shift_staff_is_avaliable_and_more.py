# Generated by Django 5.1.2 on 2024-11-18 14:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_manager_hotel_receptionist_hotel_staff_hotel'),
    ]

    operations = [
        migrations.AddField(
            model_name='manager',
            name='shift',
            field=models.CharField(choices=[('Morning', 'Morning'), ('Evening', 'Evening'), ('Night', 'Night')], default='Morning', max_length=20),
        ),
        migrations.AddField(
            model_name='receptionist',
            name='shift',
            field=models.CharField(choices=[('Morning', 'Morning'), ('Evening', 'Evening'), ('Night', 'Night')], default='Morning', max_length=20),
        ),
        migrations.AddField(
            model_name='staff',
            name='is_avaliable',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='staff',
            name='shift',
            field=models.CharField(choices=[('Morning', 'Morning'), ('Evening', 'Evening'), ('Night', 'Night')], default='Morning', max_length=20),
        ),
        migrations.AddField(
            model_name='user',
            name='salary',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='user',
            name='upi_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='user_profile',
            field=models.ImageField(blank=True, default='profile_pics/default.jpg', null=True, upload_to='profile_pics/'),
        ),
        migrations.AlterField(
            model_name='staff',
            name='department',
            field=models.CharField(max_length=40),
        ),
    ]
