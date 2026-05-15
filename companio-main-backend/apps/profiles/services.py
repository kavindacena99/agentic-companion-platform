from .models import UserProfile


def is_profile_complete(profile):
    return all([
        bool(profile.display_name),
        bool(profile.preferred_language),
        bool(profile.timezone),
    ])


def update_profile_completion(profile):
    profile.profile_completed = is_profile_complete(profile)
    profile.save(update_fields=['profile_completed', 'updated_at'])
    return profile


def create_profile_for_user(user):
    profile, _created = UserProfile.objects.get_or_create(user=user)
    update_profile_completion(profile)
    return profile
