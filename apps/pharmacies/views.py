from django.apps import apps as django_apps
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Pharmacy, PharmacyStock


@login_required
def pharmacy_list_view(request):
    """Show sample pharmacies and, optionally, stock for one medicine."""
    medicine_id = request.GET.get("medicine", "").strip()

    # String app lookup avoids a Python import from another feature app.
    Medicine = django_apps.get_model("medicines", "Medicine")
    selected_medicine = None
    if medicine_id.isdigit():
        selected_medicine = Medicine.objects.filter(pk=medicine_id).first()

    pharmacies = Pharmacy.objects.all().order_by("name")

    # Build a {pharmacy_id: in_stock} map once instead of querying per card.
    stock_by_pharmacy = {}
    if selected_medicine is not None:
        stock_by_pharmacy = {
            item.pharmacy_id: item.in_stock
            for item in PharmacyStock.objects.filter(medicine=selected_medicine)
        }

    # Pair each pharmacy with True, False, or None (None means not listed).
    pharmacy_rows = [
        {
            "pharmacy": pharmacy,
            "stock": stock_by_pharmacy.get(pharmacy.id),
        }
        for pharmacy in pharmacies
    ]

    return render(request, "pharmacies/list.html", {
        "pharmacy_rows": pharmacy_rows,
        "medicines": Medicine.objects.all().order_by("brand_name"),
        "selected_medicine": selected_medicine,
    })
