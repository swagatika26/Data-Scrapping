from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Custom User model if needed.
    """
    ROLE_ADMIN = 'ADMIN'
    ROLE_USER = 'USER'
    ROLE_CHOICES = (
        (ROLE_ADMIN, 'Admin'),
        (ROLE_USER, 'User'),
    )

    bio = models.TextField(blank=True, null=True)
    job_title = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_USER)
    is_banned = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username
