from django.apps import apps as django_apps
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Pharmacy, PharmacyStock


class PharmacyListViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="StrongPass!2026")

        Medicine = django_apps.get_model("medicines", "Medicine")
        self.medicine = Medicine.objects.create(
            brand_name="Biogesic",
            generic_name="Paracetamol",
            dosage="500 mg tablet",
            manufacturer="Unilab",
            mdrp_price="5.00",
        )

        self.pharmacy = Pharmacy.objects.create(
            name="Chong Hua Hospital Pharmacy",
            address="Fuente Osmeña Circle, Cebu City",
            latitude="10.310290",
            longitude="123.892590",
            contact_number="(032) 255 8000",
            operating_hours="Open 24 hours",
        )
        PharmacyStock.objects.create(
            pharmacy=self.pharmacy,
            medicine=self.medicine,
            in_stock=True,
        )

        self.client.force_login(self.user)

    def test_list_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("pharmacies:list"))
        self.assertEqual(response.status_code, 302)

    def test_list_shows_pharmacy_details_and_stock(self):
        response = self.client.get(
            reverse("pharmacies:list"),
            {"medicine": self.medicine.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chong Hua Hospital Pharmacy")
        self.assertContains(response, "Fuente Osmeña Circle")
        self.assertContains(response, "Open 24 hours")
        self.assertContains(response, "In stock")

    def test_directions_link_uses_coordinates(self):
        response = self.client.get(reverse("pharmacies:list"))

        self.assertContains(response, "google.com/maps/dir")
        self.assertContains(response, "destination=10.310290,123.892590")
        self.assertContains(response, "travelmode=driving")

    def test_directions_fall_back_to_the_address_without_coordinates(self):
        Pharmacy.objects.create(
            name="No Pin Pharmacy",
            address="123 Sample Street, Cebu City",
            latitude="0",
            longitude="0",
        )

        response = self.client.get(reverse("pharmacies:list"))

        self.assertContains(response, "destination=123%20Sample%20Street,%20Cebu%20City")
        self.assertNotContains(response, "destination=0,0")

    def test_without_a_medicine_stock_badges_are_hidden(self):
        response = self.client.get(reverse("pharmacies:list"))
        self.assertNotContains(response, "In stock")
        self.assertNotContains(response, "Out of stock")


class StockLedgerTests(TestCase):
    """JOIN: pharmacy_stock rows paired with their pharmacy and medicine."""

    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="StrongPass!2026")

        Medicine = django_apps.get_model("medicines", "Medicine")
        self.biogesic = Medicine.objects.create(
            brand_name="Biogesic",
            generic_name="Paracetamol",
            dosage="500 mg tablet",
            manufacturer="Unilab",
            mdrp_price="5.00",
        )
        self.pharmacy = Pharmacy.objects.create(
            name="Mercury Drug - Colon",
            address="Colon Street, Cebu City",
            latitude="10.296330",
            longitude="123.903180",
        )
        PharmacyStock.objects.create(
            pharmacy=self.pharmacy,
            medicine=self.biogesic,
            in_stock=True,
        )

        self.client.force_login(self.user)

    def test_ledger_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("pharmacies:stock"))
        self.assertEqual(response.status_code, 302)

    def test_ledger_shows_pharmacy_and_medicine_together(self):
        response = self.client.get(reverse("pharmacies:stock"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Mercury Drug - Colon")
        self.assertContains(response, "Colon Street, Cebu City")
        self.assertContains(response, "Biogesic")
        self.assertContains(response, "Paracetamol")
        self.assertContains(response, "In stock")

    def test_ledger_filters_by_status(self):
        response = self.client.get(reverse("pharmacies:stock"), {"status": "out"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No listings match that filter.")

    def test_ledger_filters_by_pharmacy(self):
        response = self.client.get(
            reverse("pharmacies:stock"), {"pharmacy": self.pharmacy.id}
        )

        self.assertContains(response, "Mercury Drug - Colon")

    def test_ledger_link_is_in_the_navigation(self):
        response = self.client.get(reverse("home:home"))
        self.assertContains(response, reverse("pharmacies:stock"))


class RestockWatchTests(TestCase):
    """SUBQUERY: pharmacies whose id appears in the out-of-stock inner query."""

    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="StrongPass!2026")

        Medicine = django_apps.get_model("medicines", "Medicine")
        self.medicine = Medicine.objects.create(
            brand_name="Lithane",
            generic_name="Lithium carbonate",
            dosage="300 mg tablet",
            manufacturer="Sample Pharma",
            mdrp_price="22.00",
        )
        self.gap_pharmacy = Pharmacy.objects.create(
            name="Cebu Doctors' University Hospital Pharmacy",
            address="Osmeña Boulevard, Cebu City",
            latitude="10.315240",
            longitude="123.889950",
        )
        self.stocked_pharmacy = Pharmacy.objects.create(
            name="Chong Hua Hospital Pharmacy",
            address="Fuente Osmeña Circle, Cebu City",
            latitude="10.310290",
            longitude="123.892590",
        )
        PharmacyStock.objects.create(
            pharmacy=self.gap_pharmacy, medicine=self.medicine, in_stock=False
        )
        PharmacyStock.objects.create(
            pharmacy=self.stocked_pharmacy, medicine=self.medicine, in_stock=True
        )

        self.client.force_login(self.user)

    def test_restock_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("pharmacies:restock"))
        self.assertEqual(response.status_code, 302)

    def test_restock_keeps_only_pharmacies_from_the_inner_query(self):
        response = self.client.get(reverse("pharmacies:restock"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cebu Doctors&#x27; University Hospital Pharmacy")
        self.assertNotContains(response, "Chong Hua Hospital Pharmacy")

    def test_restock_lists_the_out_of_stock_medicine(self):
        response = self.client.get(reverse("pharmacies:restock"))
        self.assertContains(response, "Lithane")
