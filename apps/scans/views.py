import os
from decimal import Decimal

from django.apps import apps as django_apps
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.files.storage import FileSystemStorage
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .matching import find_best_match, match_status
from .models import PrescriptionScan
from .ocr import extract_text


@login_required
def history_view(request):
    """Show only the signed-in user's scans, newest first."""
    scans = (
        PrescriptionScan.objects.filter(user=request.user)
        .select_related("matched_medicine")
        .order_by("-created_at")
    )

    return render(request, "scans/history.html", {"scans": scans})


ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024


def _validate_image(upload):
    """Return an error message, or an empty string when the upload is valid."""
    extension = os.path.splitext(upload.name)[1].lower().lstrip(".")

    if extension not in ALLOWED_EXTENSIONS:
        return "Upload a JPG, PNG, or WebP image."

    if upload.content_type not in ALLOWED_CONTENT_TYPES:
        return "That file does not look like a JPG, PNG, or WebP image."

    if upload.size > MAX_IMAGE_BYTES:
        return "The image is larger than 5 MB. Choose a smaller file."

    return ""


def _save_image(upload):
    """Store the upload under MEDIA_ROOT/scans and return a relative path."""
    storage = FileSystemStorage(
        location=os.path.join(settings.MEDIA_ROOT, "scans"),
        base_url=settings.MEDIA_URL + "scans/",
    )
    saved_name = storage.save(upload.name, upload)

    # Always store forward slashes so the path works on any machine.
    return "scans/" + saved_name.replace("\\", "/")


def _image_url(image_path):
    return settings.MEDIA_URL + image_path if image_path else ""


@login_required
def scan_view(request):
    """Accept a prescription image and/or a typed medicine name, then match it."""
    result = None
    error = ""
    typed_value = ""

    if request.method == "POST":
        typed_value = request.POST.get("medicine_name", "").strip()
        image = request.FILES.get("image")

        if image is None and not typed_value:
            error = "Choose an image or type a medicine name."
        else:
            image_error = _validate_image(image) if image else ""

            if image_error:
                error = image_error
            else:
                image_path = _save_image(image) if image else ""
                extracted_text = (
                    extract_text(os.path.join(settings.MEDIA_ROOT, image_path))
                    if image_path else ""
                )

                # A typed name is more reliable than the placeholder OCR today.
                matching_text = typed_value or extracted_text

                if not matching_text:
                    # Keep the upload in history so the user can see it was stored.
                    scan = PrescriptionScan.objects.create(
                        user=request.user,
                        image_path=image_path,
                        extracted_text="",
                        confidence_score=Decimal("0.00"),
                    )
                    result = {
                        "status": "manual",
                        "confidence": 0.0,
                        "medicine": None,
                        "scan": scan,
                        "image_url": _image_url(image_path),
                        "message": (
                            "The image was saved, but OCR is not connected yet, so no text "
                            "was read. Type the medicine name to get a match."
                        ),
                    }
                else:
                    medicine, confidence = find_best_match(matching_text)
                    status = match_status(confidence)

                    scan = PrescriptionScan.objects.create(
                        user=request.user,
                        image_path=image_path,
                        extracted_text=matching_text,
                        confidence_score=Decimal(str(round(confidence, 2))),
                        # Only a high-confidence match is saved as final.
                        matched_medicine=medicine if status == "matched" else None,
                    )

                    result = {
                        "status": status,
                        "confidence": confidence,
                        "medicine": medicine,
                        "scan": scan,
                        "image_url": _image_url(image_path),
                    }

                    if status == "matched":
                        messages.success(request, "Match saved to your scan history.")

    return render(request, "scans/scan.html", {
        "result": result,
        "error": error,
        "typed_value": typed_value,
    })


@login_required
@require_POST
def confirm_match_view(request, scan_id):
    """Save the medicine the user confirmed after a 70-90 confidence match."""
    scan = get_object_or_404(PrescriptionScan, pk=scan_id, user=request.user)

    medicine_id = request.POST.get("medicine_id", "").strip()
    if not medicine_id.isdigit():
        raise Http404("Medicine not found")

    Medicine = django_apps.get_model("medicines", "Medicine")
    medicine = get_object_or_404(Medicine, pk=medicine_id)

    scan.matched_medicine = medicine
    scan.save(update_fields=["matched_medicine"])

    messages.success(request, "Match confirmed. Showing its generic alternatives.")
    return redirect(reverse("home:home") + "?medicine=" + str(medicine.id))
