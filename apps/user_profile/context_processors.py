from .models import Profile


def user_avatar(request):
    """Expose the signed-in user's avatar to every template.

    The navigation bar needs the photo on every page, and a reverse one-to-one
    raises when an account has no Profile row yet, so getattr covers both.
    """
    if not request.user.is_authenticated:
        return {"user_avatar_url": "", "user_initial": ""}

    profile = getattr(request.user, "profile", None)
    avatar_url = profile.avatar.url if profile and profile.avatar else ""

    return {
        "user_avatar_url": avatar_url,
        "user_initial": request.user.username[:1].upper(),
    }
