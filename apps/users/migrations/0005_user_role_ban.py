from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_user_otp_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('ADMIN', 'Admin'), ('USER', 'User')], default='USER', max_length=10),
        ),
        migrations.AddField(
            model_name='user',
            name='is_banned',
            field=models.BooleanField(default=False),
        ),
    ]
