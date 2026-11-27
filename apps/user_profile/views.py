from PIL import Image, UnidentifiedImageError

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .models import Profile

MAX_AVATAR_BYTES = 2 * 1024 * 1024
MAX_AVATAR_PIXELS = 40_000_000
ALLOWED_AVATAR_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_AVATAR_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}


def _validate_avatar(upload):
    """Return an error message, or an empty string when the image is usable."""
    extension = upload.name.rsplit(".", 1)[-1].lower() if "." in upload.name else ""

    if extension not in ALLOWED_AVATAR_EXTENSIONS:
        return "Choose a JPG, PNG, or WebP image."

    if upload.content_type not in ALLOWED_AVATAR_TYPES:
        return "That file does not look like a JPG, PNG, or WebP image."

    if upload.size > MAX_AVATAR_BYTES:
        return "The photo is larger than 2 MB. Choose a smaller file."

    try:
        # verify() checks the file signature without decoding every pixel.
        with Image.open(upload) as image:
            image.verify()
    except (UnidentifiedImageError, OSError, ValueError):
        return "That file could not be read as an image."
    finally:
        upload.seek(0)

    try:
        # verify() leaves the file unusable, so reopen for the dimensions.
        with Image.open(upload) as image:
            width, height = image.size
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        return "That file could not be read as an image."
    finally:
        upload.seek(0)

    if width * height > MAX_AVATAR_PIXELS:
        return "That image is too large. Use one under 40 megapixels."

    return ""


@login_required
def profile_view(request):
    # get_or_create keeps the page usable for accounts made before profiles existed.
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        bio = request.POST.get("bio", "").strip()
        avatar = request.FILES.get("avatar")
        remove_avatar = request.POST.get("remove_avatar") == "on"

        error = _validate_avatar(avatar) if avatar else ""

        if error:
            # Keep what the user typed so the form does not reset on an error.
            profile.full_name = full_name
            profile.bio = bio
            return render(request, "profile/profile.html", {
                "profile": profile,
                "error": error,
            })

        old_avatar = profile.avatar
        profile.full_name = full_name
        profile.bio = bio

        if remove_avatar and not avatar:
            profile.avatar = ""
        elif avatar:
            profile.avatar = avatar

        profile.save()

        # Only delete the previous file after the new one is safely stored.
        if old_avatar and old_avatar.name and old_avatar.name != profile.avatar.name:
            old_avatar.delete(save=False)

        if avatar:
            messages.success(request, "Profile photo updated.")
        elif remove_avatar:
            messages.success(request, "Profile photo removed.")
        else:
            messages.success(request, "Profile saved.")

        return redirect("user_profile:profile")

    return render(request, "profile/profile.html", {"profile": profile})
