"""Prints the SQL that the JOIN and SUBQUERY features send to the database.

Run it before recording the demonstration video:

    python manage.py show_sql
"""

from django.core.management.base import BaseCommand
from django.db.models import Subquery

from apps.pharmacies.models import Pharmacy, PharmacyStock


class Command(BaseCommand):
    help = "Show the generated SQL for the stock ledger JOIN and restock SUBQUERY."

    def handle(self, *args, **options):
        join_query = (
            PharmacyStock.objects.select_related("pharmacy", "medicine")
            .order_by("pharmacy__name", "medicine__brand_name")
        )
        out_of_stock_pharmacy_ids = (
            PharmacyStock.objects.filter(in_stock=False).values("pharmacy_id")
        )
        subquery = (
            Pharmacy.objects.filter(id__in=Subquery(out_of_stock_pharmacy_ids))
            .order_by("name")
        )

        self.stdout.write(self.style.MIGRATE_HEADING("1) JOIN - stock ledger"))
        self.stdout.write(
            "PharmacyStock.objects.select_related('pharmacy', 'medicine')"
        )
        self.stdout.write("")
        self.stdout.write(str(join_query.query))
        self.stdout.write("")
        self.stdout.write(f"Rows returned: {join_query.count()}")
        self.stdout.write("")

        self.stdout.write(self.style.MIGRATE_HEADING("2) SUBQUERY - restock watch"))
        self.stdout.write(
            "Pharmacy.objects.filter(id__in=Subquery("
            "PharmacyStock.objects.filter(in_stock=False).values('pharmacy_id')))"
        )
        self.stdout.write("")
        self.stdout.write(str(subquery.query))
        self.stdout.write("")
        self.stdout.write(f"Rows returned: {subquery.count()}")
        self.stdout.write("")
