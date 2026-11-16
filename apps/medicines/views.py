from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from .models import Medicine


def _medicine_data(medicine):
    """Turn one Medicine row into JSON-friendly data for the home page."""
    return {
        "id": medicine.id,
        "brand_name": medicine.brand_name,
        "generic_name": medicine.generic_name,
        "dosage": medicine.dosage,
        "manufacturer": medicine.manufacturer,
        "rx_required": medicine.rx_required,
        "nti_warning": medicine.nti_warning,
        "mdrp_price": str(medicine.mdrp_price),
    }


@login_required
def search_view(request):
    """GET /medicines/search/?q=... returns up to 10 matching medicines."""
    query = request.GET.get("q", "").strip()

    # An empty search should not return the whole table.
    if not query:
        return JsonResponse({"results": []})

    # Search either the brand name or the generic name.
    medicines = (
        Medicine.objects.filter(
            Q(brand_name__icontains=query) | Q(generic_name__icontains=query)
        )
        .order_by("brand_name")[:10]
    )

    return JsonResponse({"results": [_medicine_data(item) for item in medicines]})


@login_required
def generics_view(request, medicine_id):
    """GET /medicines/<id>/generics/ returns one medicine and its generics."""
    medicine = get_object_or_404(Medicine, pk=medicine_id)

    # Cheapest generic alternative first helps the user compare quickly.
    alternatives = medicine.generic_alternatives.all().order_by("price")

    generics = [
        {
            "id": alternative.id,
            "name": alternative.generic_brand_name,
            "manufacturer": alternative.manufacturer,
            "price": str(alternative.price),
        }
        for alternative in alternatives
    ]

    return JsonResponse({
        "medicine": _medicine_data(medicine),
        "generics": generics,
    })
