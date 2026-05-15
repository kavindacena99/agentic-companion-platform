from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .services import create_profile_for_user


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        create_profile_for_user(instance)
