from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import User
from .utils.email_utils import send_login_credentials, send_email_changed_notification

@receiver(post_save, sender=User)
def send_user_credentials_on_create(sender, instance, created, **kwargs):
    """Send HTML credentials email after user creation"""
    if created and instance.email:
        # You can store the raw password in the serializer temporarily or use a random one
        password = getattr(instance, "_raw_password", None) or "Your chosen password"
        send_login_credentials(instance.email, instance.username, password)


@receiver(pre_save, sender=User)
def notify_email_change(sender, instance, **kwargs):
    """Detect and notify when user's email changes"""
    if instance.pk:
        old_user = User.objects.get(pk=instance.pk)
        if old_user.email != instance.email and instance.email:
            send_email_changed_notification(instance.username, old_user.email, instance.email)
