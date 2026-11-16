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

    def test_without_a_medicine_stock_badges_are_hidden(self):
        response = self.client.get(reverse("pharmacies:list"))
        self.assertNotContains(response, "In stock")
        self.assertNotContains(response, "Out of stock")
