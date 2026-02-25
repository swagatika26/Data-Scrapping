from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_admin_user(apps, schema_editor):
    User = apps.get_model('users', 'User')
    username = 'admin'
    email = 'admin@scrapyx.local'
    password = make_password('Admin@12345')
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': email,
            'password': password,
            'is_active': True,
            'role': 'ADMIN',
            'is_banned': False,
        },
    )
    if not created:
        User.objects.filter(pk=user.pk).update(
            email=email,
            password=password,
            is_active=True,
            role='ADMIN',
            is_banned=False,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_user_role_ban'),
    ]

    operations = [
        migrations.RunPython(create_admin_user),
    ]
