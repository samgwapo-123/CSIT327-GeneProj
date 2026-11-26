from django.apps import apps as django_apps
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Subquery
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


@login_required
def stock_ledger_view(request):
    """SQL JOIN: every stock row together with its pharmacy and medicine."""
    pharmacy_id = request.GET.get("pharmacy", "").strip()
    status = request.GET.get("status", "").strip()

    # select_related turns both foreign keys into SQL INNER JOINs, so the
    # pharmacy and medicine rows arrive in the same query instead of one
    # extra lookup per listing.
    listings = PharmacyStock.objects.select_related("pharmacy", "medicine")

    if pharmacy_id.isdigit():
        listings = listings.filter(pharmacy_id=pharmacy_id)
    if status == "in":
        listings = listings.filter(in_stock=True)
    elif status == "out":
        listings = listings.filter(in_stock=False)

    # The template groups rows by pharmacy, so that column must lead the sort.
    listings = listings.order_by("pharmacy__name", "medicine__brand_name")

    return render(request, "pharmacies/stock.html", {
        "listings": listings,
        "pharmacies": Pharmacy.objects.order_by("name"),
        "selected_pharmacy": pharmacy_id,
        "selected_status": status,
    })


@login_required
def restock_watch_view(request):
    """SQL SUBQUERY: pharmacies with at least one medicine out of stock."""
    # Inner query: only the pharmacy_id column, from out-of-stock rows.
    out_of_stock_pharmacy_ids = (
        PharmacyStock.objects.filter(in_stock=False).values("pharmacy_id")
    )

    # Outer query: keep only the pharmacies whose id appears in that result.
    pharmacies = (
        Pharmacy.objects.filter(id__in=Subquery(out_of_stock_pharmacy_ids))
        .prefetch_related(
            Prefetch(
                "stock_items",
                queryset=PharmacyStock.objects.filter(in_stock=False).select_related(
                    "medicine"
                ),
                to_attr="gap_items",
            )
        )
        .order_by("name")
    )

    return render(request, "pharmacies/restock.html", {
        "pharmacies": pharmacies,
        "total_pharmacies": Pharmacy.objects.count(),
    })
