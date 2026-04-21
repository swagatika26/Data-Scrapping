from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.contrib.sessions.models import Session
from django.utils import timezone
from django.contrib.auth.models import User as DjangoUser
from django.db import connection

@receiver(pre_delete, sender=DjangoUser)
def cleanup_user_data(sender, instance, **kwargs):
    """
    Signal handler to clean up all related data when a user is deleted.
    This ensures foreign key constraints are handled properly.
    """
    try:
        # Kill active sessions for the user
        for session in Session.objects.filter(expire_date__gte=timezone.now()):
            data = session.get_decoded()
            if str(data.get('_auth_user_id')) == str(instance.id):
                session.delete()
        
        # Use raw SQL to handle any remaining foreign key constraints
        with connection.cursor() as cursor:
            # Disable foreign key constraints temporarily
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            try:
                # Delete allauth data if tables exist
                cursor.execute("DELETE FROM account_emailaddress WHERE user_id = %s", [instance.id])
            except:
                pass
            
            try:
                cursor.execute("DELETE FROM socialaccount_socialaccount WHERE user_id = %s", [instance.id])
            except:
                pass
            
            # Delete billing data if table exists
            try:
                cursor.execute("DELETE FROM billing_invoice WHERE user_id = %s", [instance.id])
            except:
                pass
            
            # Delete Django auth relationships
            cursor.execute("DELETE FROM users_user_permissions WHERE user_id = %s", [instance.id])
            cursor.execute("DELETE FROM users_groups WHERE user_id = %s", [instance.id])
            
            # Delete Django admin logs
            cursor.execute("DELETE FROM django_admin_log WHERE user_id = %s", [instance.id])
            
            # Re-enable foreign key constraints
            cursor.execute("PRAGMA foreign_keys = ON")
            
    except Exception:
        # Don't prevent user deletion if cleanup fails
        pass
