from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Custom User model if needed.
    """
    bio = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'users'

    def __str__(self):
        return self.username
