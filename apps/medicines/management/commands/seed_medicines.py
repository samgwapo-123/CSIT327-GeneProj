from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.medicines.models import GenericAlternative, Medicine


# SAMPLE DATA ONLY. These prices are made up for the CSIT327 demo and are
# not official Maximum Drug Retail Price (MDRP) figures.
MEDICINES = [
    {
        "brand_name": "Biogesic",
        "generic_name": "Paracetamol",
        "dosage": "500 mg tablet",
        "manufacturer": "Unilab",
        "rx_required": False,
        "nti_warning": False,
        "mdrp_price": "5.00",
        "generics": [
            ("RiteMed Paracetamol", "RiteMed", "2.50"),
            ("TGP Paracetamol", "The Generics Pharmacy", "2.75"),
            ("Medhaus Paracetamol", "Medhaus", "2.40"),
        ],
    },
    {
        "brand_name": "Medicol Advance",
        "generic_name": "Ibuprofen",
        "dosage": "200 mg capsule",
        "manufacturer": "Unilab",
        "rx_required": False,
        "nti_warning": False,
        "mdrp_price": "6.00",
        "generics": [
            ("RiteMed Ibuprofen", "RiteMed", "3.00"),
            ("TGP Ibuprofen", "The Generics Pharmacy", "3.25"),
        ],
    },
    {
        "brand_name": "Alaxan FR",
        "generic_name": "Ibuprofen + Paracetamol",
        "dosage": "200 mg/325 mg capsule",
        "manufacturer": "Unilab",
        "rx_required": False,
        "nti_warning": False,
        "mdrp_price": "7.00",
        "generics": [
            ("RiteMed Ibuprofen + Paracetamol", "RiteMed", "3.75"),
            ("Medhaus Ibuprofen + Paracetamol", "Medhaus", "4.00"),
        ],
    },
    {
        "brand_name": "Neozep Forte",
        "generic_name": "Phenylephrine + Chlorphenamine",
        "dosage": "10 mg/2 mg tablet",
        "manufacturer": "Unilab",
        "rx_required": False,
        "nti_warning": False,
        "mdrp_price": "6.50",
        "generics": [
            ("RiteMed Phenylephrine + Chlorphenamine", "RiteMed", "3.50"),
            ("TGP Phenylephrine + Chlorphenamine", "The Generics Pharmacy", "3.25"),
        ],
    },
    {
        "brand_name": "Bioflu",
        "generic_name": "Paracetamol + Phenylephrine + Chlorphenamine",
        "dosage": "250 mg/5 mg/2 mg tablet",
        "manufacturer": "Unilab",
        "rx_required": False,
        "nti_warning": False,
        "mdrp_price": "8.00",
        "generics": [
            ("RiteMed Paracetamol + Phenylephrine + Chlorphenamine", "RiteMed", "4.50"),
            ("TGP Paracetamol + Phenylephrine + Chlorphenamine", "The Generics Pharmacy", "4.25"),
        ],
    },
    {
        "brand_name": "Solmux",
        "generic_name": "Carbocisteine",
        "dosage": "500 mg capsule",
        "manufacturer": "Unilab",
        "rx_required": False,
        "nti_warning": False,
        "mdrp_price": "9.00",
        "generics": [
            ("RiteMed Carbocisteine", "RiteMed", "5.00"),
            ("TGP Carbocisteine", "The Generics Pharmacy", "5.25"),
        ],
    },
    {
        "brand_name": "Zyrtec",
        "generic_name": "Cetirizine",
        "dosage": "10 mg tablet",
        "manufacturer": "Johnson & Johnson",
        "rx_required": False,
        "nti_warning": False,
        "mdrp_price": "12.00",
        "generics": [
            ("RiteMed Cetirizine", "RiteMed", "4.00"),
            ("TGP Cetirizine", "The Generics Pharmacy", "3.75"),
            ("Medhaus Cetirizine", "Medhaus", "3.50"),
        ],
    },
    {
        "brand_name": "Kremil-S",
        "generic_name": "Aluminum hydroxide + Magnesium hydroxide + Simethicone",
        "dosage": "200 mg/200 mg/20 mg tablet",
        "manufacturer": "Unilab",
        "rx_required": False,
        "nti_warning": False,
        "mdrp_price": "7.50",
        "generics": [
            ("RiteMed Aluminum + Magnesium + Simethicone", "RiteMed", "4.00"),
            ("TGP Aluminum + Magnesium + Simethicone", "The Generics Pharmacy", "4.25"),
        ],
    },
    {
        "brand_name": "Diatabs",
        "generic_name": "Loperamide",
        "dosage": "2 mg capsule",
        "manufacturer": "Unilab",
        "rx_required": False,
        "nti_warning": False,
        "mdrp_price": "6.00",
        "generics": [
            ("RiteMed Loperamide", "RiteMed", "2.50"),
            ("TGP Loperamide", "The Generics Pharmacy", "2.25"),
        ],
    },
    {
        "brand_name": "Cozaar",
        "generic_name": "Losartan potassium",
        "dosage": "50 mg tablet",
        "manufacturer": "MSD",
        "rx_required": True,
        "nti_warning": False,
        "mdrp_price": "18.00",
        "generics": [
            ("RiteMed Losartan", "RiteMed", "7.00"),
            ("TGP Losartan", "The Generics Pharmacy", "6.50"),
            ("Medhaus Losartan", "Medhaus", "6.75"),
        ],
    },
    {
        "brand_name": "Norvasc",
        "generic_name": "Amlodipine",
        "dosage": "5 mg tablet",
        "manufacturer": "Pfizer",
        "rx_required": True,
        "nti_warning": False,
        "mdrp_price": "20.00",
        "generics": [
            ("RiteMed Amlodipine", "RiteMed", "5.00"),
            ("TGP Amlodipine", "The Generics Pharmacy", "4.75"),
            ("Hizon Amlodipine", "Hizon Laboratories", "5.25"),
        ],
    },
    {
        "brand_name": "Glucophage",
        "generic_name": "Metformin",
        "dosage": "500 mg tablet",
        "manufacturer": "Merck",
        "rx_required": True,
        "nti_warning": False,
        "mdrp_price": "12.00",
        "generics": [
            ("RiteMed Metformin", "RiteMed", "5.50"),
            ("TGP Metformin", "The Generics Pharmacy", "5.25"),
        ],
    },
    {
        "brand_name": "Lipitor",
        "generic_name": "Atorvastatin",
        "dosage": "20 mg tablet",
        "manufacturer": "Pfizer",
        "rx_required": True,
        "nti_warning": False,
        "mdrp_price": "25.00",
        "generics": [
            ("RiteMed Atorvastatin", "RiteMed", "9.00"),
            ("TGP Atorvastatin", "The Generics Pharmacy", "8.50"),
        ],
    },
    {
        "brand_name": "Coumadin",
        "generic_name": "Warfarin sodium",
        "dosage": "5 mg tablet",
        "manufacturer": "Bristol-Myers Squibb",
        "rx_required": True,
        "nti_warning": True,
        "mdrp_price": "30.00",
        "generics": [
            ("RiteMed Warfarin", "RiteMed", "12.00"),
            ("Zydus Warfarin", "Zydus Pharma", "13.50"),
        ],
    },
    {
        "brand_name": "Lanoxin",
        "generic_name": "Digoxin",
        "dosage": "0.25 mg tablet",
        "manufacturer": "Aspen",
        "rx_required": True,
        "nti_warning": True,
        "mdrp_price": "15.00",
        "generics": [
            ("RiteMed Digoxin", "RiteMed", "6.00"),
            ("TGP Digoxin", "The Generics Pharmacy", "5.75"),
        ],
    },
    {
        "brand_name": "Lithane",
        "generic_name": "Lithium carbonate",
        "dosage": "300 mg tablet",
        "manufacturer": "Aspen",
        "rx_required": True,
        "nti_warning": True,
        "mdrp_price": "22.00",
        "generics": [
            ("RiteMed Lithium carbonate", "RiteMed", "9.50"),
            ("TGP Lithium carbonate", "The Generics Pharmacy", "9.00"),
        ],
    },
    {
        "brand_name": "Dilantin",
        "generic_name": "Phenytoin sodium",
        "dosage": "100 mg capsule",
        "manufacturer": "Pfizer",
        "rx_required": True,
        "nti_warning": True,
        "mdrp_price": "18.00",
        "generics": [
            ("RiteMed Phenytoin", "RiteMed", "7.00"),
            ("TGP Phenytoin", "The Generics Pharmacy", "6.75"),
        ],
    },
    {
        "brand_name": "Augmentin",
        "generic_name": "Amoxicillin + Clavulanic acid",
        "dosage": "500 mg/125 mg tablet",
        "manufacturer": "GlaxoSmithKline",
        "rx_required": True,
        "nti_warning": False,
        "mdrp_price": "45.00",
        "generics": [
            ("RiteMed Amoxicillin + Clavulanic acid", "RiteMed", "22.00"),
            ("TGP Amoxicillin + Clavulanic acid", "The Generics Pharmacy", "20.50"),
        ],
    },
    {
        "brand_name": "Losec",
        "generic_name": "Omeprazole",
        "dosage": "20 mg capsule",
        "manufacturer": "AstraZeneca",
        "rx_required": True,
        "nti_warning": False,
        "mdrp_price": "28.00",
        "generics": [
            ("RiteMed Omeprazole", "RiteMed", "8.00"),
            ("TGP Omeprazole", "The Generics Pharmacy", "7.50"),
        ],
    },
    {
        "brand_name": "Ventolin",
        "generic_name": "Salbutamol",
        "dosage": "2 mg tablet",
        "manufacturer": "GlaxoSmithKline",
        "rx_required": True,
        "nti_warning": False,
        "mdrp_price": "10.00",
        "generics": [
            ("RiteMed Salbutamol", "RiteMed", "4.00"),
            ("TGP Salbutamol", "The Generics Pharmacy", "3.75"),
        ],
    },
]


class Command(BaseCommand):
    help = "Create or refresh sample GeneRX medicines and generic alternatives (idempotent)."

    def handle(self, *args, **options):
        medicine_count = 0
        generic_count = 0

        for row in MEDICINES:
            # update_or_create keeps the command safe to run more than once.
            medicine, _created = Medicine.objects.update_or_create(
                brand_name=row["brand_name"],
                defaults={
                    "generic_name": row["generic_name"],
                    "dosage": row["dosage"],
                    "manufacturer": row["manufacturer"],
                    "rx_required": row["rx_required"],
                    "nti_warning": row["nti_warning"],
                    "mdrp_price": Decimal(row["mdrp_price"]),
                },
            )
            medicine_count += 1

            for generic_name, manufacturer, price in row["generics"]:
                GenericAlternative.objects.update_or_create(
                    medicine=medicine,
                    generic_brand_name=generic_name,
                    defaults={
                        "manufacturer": manufacturer,
                        "price": Decimal(price),
                    },
                )
                generic_count += 1

        self.stdout.write(self.style.SUCCESS(
            "Seeded %d medicines and %d generic alternatives." % (medicine_count, generic_count)
        ))
        self.stdout.write(self.style.WARNING(
            "Reminder: all prices are sample data for this class project, not official MDRP prices."
        ))
