from django.apps import apps as django_apps
from django.core.management.base import BaseCommand

from apps.pharmacies.models import Pharmacy, PharmacyStock


# SAMPLE DATA ONLY. These are fictional Cebu City entries for the class demo.
PHARMACIES = [
    {
        "name": "Chong Hua Hospital Pharmacy",
        "address": "Fuente Osmeña Circle, Cebu City",
        "latitude": "10.310290",
        "longitude": "123.892590",
        "contact_number": "(032) 255 8000",
        "operating_hours": "Open 24 hours",
        "stock": [
            ("Biogesic", True),
            ("Coumadin", True),
            ("Lanoxin", True),
            ("Cozaar", True),
        ],
    },
    {
        "name": "Cebu Doctors' University Hospital Pharmacy",
        "address": "Osmeña Boulevard, Cebu City",
        "latitude": "10.315240",
        "longitude": "123.889950",
        "contact_number": "(032) 255 5555",
        "operating_hours": "Open 24 hours",
        "stock": [
            ("Biogesic", True),
            ("Coumadin", True),
            ("Dilantin", True),
            ("Lithane", False),
        ],
    },
    {
        "name": "Mercury Drug - Colon",
        "address": "Colon Street, Cebu City",
        "latitude": "10.296330",
        "longitude": "123.903180",
        "contact_number": "(032) 253 1234",
        "operating_hours": "7:00 AM - 10:00 PM",
        "stock": [
            ("Biogesic", True),
            ("Alaxan FR", True),
            ("Neozep Forte", True),
            ("Bioflu", True),
            ("Solmux", True),
        ],
    },
    {
        "name": "Watsons - Ayala Center Cebu",
        "address": "Ayala Center Cebu, Cebu Business Park, Cebu City",
        "latitude": "10.318450",
        "longitude": "123.905090",
        "contact_number": "(032) 231 5678",
        "operating_hours": "10:00 AM - 9:00 PM",
        "stock": [
            ("Zyrtec", True),
            ("Kremil-S", True),
            ("Diatabs", True),
            ("Losec", True),
            ("Ventolin", True),
        ],
    },
    {
        "name": "Rose Pharmacy - Mango Avenue",
        "address": "Mango Avenue, Cebu City",
        "latitude": "10.315680",
        "longitude": "123.899220",
        "contact_number": "(032) 254 7890",
        "operating_hours": "8:00 AM - 10:00 PM",
        "stock": [
            ("Cozaar", True),
            ("Norvasc", True),
            ("Glucophage", True),
            ("Lipitor", True),
        ],
    },
    {
        "name": "Generika Drugstore - Labangon",
        "address": "Labangon, Cebu City",
        "latitude": "10.296540",
        "longitude": "123.880110",
        "contact_number": "(032) 262 3456",
        "operating_hours": "8:00 AM - 8:00 PM",
        "stock": [
            ("Biogesic", True),
            ("Cozaar", True),
            ("Norvasc", True),
            ("Glucophage", True),
            ("Lipitor", False),
        ],
    },
    {
        "name": "St. Vincent Pharmacy - Sambag",
        "address": "Sambag I, Cebu City",
        "latitude": "10.301120",
        "longitude": "123.890350",
        "contact_number": "(032) 256 2345",
        "operating_hours": "8:00 AM - 9:00 PM",
        "stock": [
            ("Biogesic", True),
            ("Medicol Advance", True),
            ("Solmux", True),
            ("Diatabs", True),
        ],
    },
    {
        "name": "Cebu City Health Office Pharmacy",
        "address": "Cebu City Health Office, Cebu City",
        "latitude": "10.309050",
        "longitude": "123.893130",
        "contact_number": "(032) 411 1234",
        "operating_hours": "8:00 AM - 5:00 PM",
        "stock": [
            ("Biogesic", True),
            ("Coumadin", False),
            ("Lanoxin", True),
            ("Dilantin", True),
            ("Lithane", True),
        ],
    },
]


class Command(BaseCommand):
    help = "Create or refresh sample Cebu City pharmacies and their stock (idempotent)."

    def handle(self, *args, **options):
        Medicine = django_apps.get_model("medicines", "Medicine")

        pharmacy_count = 0
        stock_count = 0
        missing_brands = set()

        for row in PHARMACIES:
            pharmacy, _created = Pharmacy.objects.update_or_create(
                name=row["name"],
                defaults={
                    "address": row["address"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "contact_number": row["contact_number"],
                    "operating_hours": row["operating_hours"],
                },
            )
            pharmacy_count += 1

            for brand_name, in_stock in row["stock"]:
                medicine = Medicine.objects.filter(brand_name=brand_name).first()

                if medicine is None:
                    missing_brands.add(brand_name)
                    continue

                PharmacyStock.objects.update_or_create(
                    pharmacy=pharmacy,
                    medicine=medicine,
                    defaults={"in_stock": in_stock},
                )
                stock_count += 1

        self.stdout.write(self.style.SUCCESS(
            "Seeded %d pharmacies and %d stock rows." % (pharmacy_count, stock_count)
        ))

        if missing_brands:
            self.stdout.write(self.style.WARNING(
                "Skipped brands that are not in the medicines table: %s. "
                "Run seed_medicines first." % ", ".join(sorted(missing_brands))
            ))

        self.stdout.write(self.style.WARNING(
            "Reminder: pharmacy names, addresses, and stock are sample data, not live information."
        ))
