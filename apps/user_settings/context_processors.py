from .models import UserSettings


def genrx_settings(request):
    """Expose the signed-in user's settings to every template.

    The view only reads, so a first-time visitor without a row simply gets None.
    """
    if not request.user.is_authenticated:
        return {"genrx_settings": None}

    return {
        "genrx_settings": UserSettings.objects.filter(user=request.user).first(),
    }
