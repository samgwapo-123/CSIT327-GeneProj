from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import GenericAlternative, Medicine


class MedicineEndpointTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="StrongPass!2026")
        self.medicine = Medicine.objects.create(
            brand_name="Biogesic",
            generic_name="Paracetamol",
            dosage="500 mg tablet",
            manufacturer="Unilab",
            mdrp_price="5.00",
        )
        GenericAlternative.objects.create(
            medicine=self.medicine,
            generic_brand_name="RiteMed Paracetamol",
            manufacturer="RiteMed",
            price="2.50",
        )
        self.client.force_login(self.user)

    def test_search_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("medicines:search"), {"q": "biogesic"})
        self.assertEqual(response.status_code, 302)

    def test_search_by_brand_name(self):
        response = self.client.get(reverse("medicines:search"), {"q": "biogesic"})
        self.assertEqual(response.status_code, 200)

        results = response.json()["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["brand_name"], "Biogesic")
        self.assertEqual(results[0]["mdrp_price"], "5.00")

    def test_search_by_generic_name(self):
        response = self.client.get(reverse("medicines:search"), {"q": "paracetamol"})
        self.assertEqual(len(response.json()["results"]), 1)

    def test_empty_search_returns_no_rows(self):
        response = self.client.get(reverse("medicines:search"))
        self.assertEqual(response.json()["results"], [])

    def test_search_returns_at_most_ten_rows(self):
        for index in range(11):
            Medicine.objects.create(
                brand_name="Testmed %02d" % index,
                generic_name="Test Generic",
                dosage="1 mg tablet",
                manufacturer="Test Labs",
                mdrp_price="1.00",
            )

        response = self.client.get(reverse("medicines:search"), {"q": "testmed"})
        self.assertEqual(len(response.json()["results"]), 10)

    def test_generics_include_medicine_price(self):
        response = self.client.get(
            reverse("medicines:generics", args=[self.medicine.id])
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["medicine"]["brand_name"], "Biogesic")
        self.assertEqual(data["medicine"]["mdrp_price"], "5.00")
        self.assertEqual(len(data["generics"]), 1)
        self.assertEqual(data["generics"][0]["price"], "2.50")

    def test_unknown_medicine_returns_404(self):
        response = self.client.get(reverse("medicines:generics", args=[99999]))
        self.assertEqual(response.status_code, 404)
