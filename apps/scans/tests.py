import os
import shutil
import tempfile
from decimal import Decimal

from django.apps import apps as django_apps
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .matching import find_best_match, match_status
from .models import PrescriptionScan
from .ocr import extract_text


class ExtractTextTests(SimpleTestCase):
    def test_placeholder_returns_empty_string(self):
        self.assertEqual(extract_text("C:/fake/prescription.png"), "")


class MatchingTests(TestCase):
    def setUp(self):
        Medicine = django_apps.get_model("medicines", "Medicine")
        self.medicine = Medicine.objects.create(
            brand_name="Biogesic",
            generic_name="Paracetamol",
            dosage="500 mg tablet",
            manufacturer="Unilab",
            mdrp_price="5.00",
        )

    def test_exact_brand_name_is_above_ninety(self):
        medicine, confidence = find_best_match("Biogesic")
        self.assertEqual(medicine, self.medicine)
        self.assertGreater(confidence, 90)

    def test_small_typo_is_in_the_confirm_range(self):
        medicine, confidence = find_best_match("Biogesik")
        self.assertEqual(medicine, self.medicine)
        self.assertGreaterEqual(confidence, 70)
        self.assertLessEqual(confidence, 90)

    def test_unrelated_text_is_below_seventy(self):
        medicine, confidence = find_best_match("qqqqqqqq")
        self.assertLess(confidence, 70)

    def test_status_boundaries(self):
        self.assertEqual(match_status(90.01), "matched")
        self.assertEqual(match_status(90), "confirm")
        self.assertEqual(match_status(70), "confirm")
        self.assertEqual(match_status(69.99), "manual")


class ScanViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="StrongPass!2026")
        self.other = User.objects.create_user(username="bob", password="StrongPass!2026")

        Medicine = django_apps.get_model("medicines", "Medicine")
        self.medicine = Medicine.objects.create(
            brand_name="Biogesic",
            generic_name="Paracetamol",
            dosage="500 mg tablet",
            manufacturer="Unilab",
            mdrp_price="5.00",
        )

        self.client.force_login(self.user)

        # Keep test uploads out of the real media/ folder.
        self.media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media_root, True)
        self.media_override = override_settings(MEDIA_ROOT=self.media_root)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)

    def valid_upload(self, name="prescription.png"):
        return SimpleUploadedFile(
            name,
            b"\x89PNG\r\n\x1a\nnot-a-real-image",
            content_type="image/png",
        )

    def test_scan_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("scans:scan"))
        self.assertEqual(response.status_code, 302)

    def test_high_confidence_match_is_saved(self):
        response = self.client.post(reverse("scans:scan"), {"medicine_name": "Biogesic"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Match found")

        scan = PrescriptionScan.objects.get(user=self.user)
        self.assertEqual(scan.matched_medicine, self.medicine)
        self.assertGreater(scan.confidence_score, Decimal("90"))

    def test_mid_confidence_requires_confirmation(self):
        response = self.client.post(reverse("scans:scan"), {"medicine_name": "Biogesik"})

        self.assertContains(response, "Needs confirmation")

        scan = PrescriptionScan.objects.get(user=self.user)
        self.assertIsNone(scan.matched_medicine)
        self.assertGreaterEqual(scan.confidence_score, Decimal("70"))
        self.assertLessEqual(scan.confidence_score, Decimal("90"))

        confirm_response = self.client.post(
            reverse("scans:confirm", args=[scan.id]),
            {"medicine_id": self.medicine.id},
        )

        self.assertRedirects(
            confirm_response,
            reverse("home:home") + "?medicine=" + str(self.medicine.id),
        )
        scan.refresh_from_db()
        self.assertEqual(scan.matched_medicine, self.medicine)

    def test_low_confidence_asks_for_manual_entry(self):
        response = self.client.post(reverse("scans:scan"), {"medicine_name": "qqqqqqqq"})

        self.assertContains(response, "We need a clearer name")

        scan = PrescriptionScan.objects.get(user=self.user)
        self.assertIsNone(scan.matched_medicine)
        self.assertLess(scan.confidence_score, Decimal("70"))

    def test_image_upload_is_stored(self):
        response = self.client.post(reverse("scans:scan"), {
            "medicine_name": "Biogesic",
            "image": self.valid_upload(),
        })

        self.assertEqual(response.status_code, 200)

        scan = PrescriptionScan.objects.get(user=self.user)
        self.assertTrue(scan.image_path.startswith("scans/"))
        self.assertTrue(os.path.exists(os.path.join(self.media_root, scan.image_path)))

    def test_image_without_typed_name_is_honest_about_ocr(self):
        response = self.client.post(reverse("scans:scan"), {
            "medicine_name": "",
            "image": self.valid_upload(),
        })

        self.assertContains(response, "OCR is not connected")

        scan = PrescriptionScan.objects.get(user=self.user)
        self.assertEqual(scan.extracted_text, "")
        self.assertEqual(scan.confidence_score, Decimal("0.00"))
        self.assertIsNone(scan.matched_medicine)

    def test_oversized_image_is_rejected(self):
        big_upload = SimpleUploadedFile(
            "big.png",
            b"x" * (5 * 1024 * 1024 + 1),
            content_type="image/png",
        )

        response = self.client.post(reverse("scans:scan"), {"image": big_upload})

        self.assertContains(response, "larger than 5 MB")
        self.assertEqual(PrescriptionScan.objects.count(), 0)

    def test_unsupported_file_type_is_rejected(self):
        gif_upload = SimpleUploadedFile("photo.gif", b"GIF89a", content_type="image/gif")

        response = self.client.post(reverse("scans:scan"), {"image": gif_upload})

        self.assertContains(response, "Upload a JPG, PNG, or WebP image.")
        self.assertEqual(PrescriptionScan.objects.count(), 0)

    def test_history_only_shows_current_users_scans(self):
        PrescriptionScan.objects.create(
            user=self.user,
            image_path="",
            extracted_text="my-own-scan",
            confidence_score="100.00",
            matched_medicine=self.medicine,
        )
        PrescriptionScan.objects.create(
            user=self.other,
            image_path="",
            extracted_text="private-other-scan",
            confidence_score="95.00",
            matched_medicine=self.medicine,
        )

        response = self.client.get(reverse("scans:history"))

        self.assertContains(response, "my-own-scan")
        self.assertNotContains(response, "private-other-scan")

    def test_cannot_confirm_another_users_scan(self):
        scan = PrescriptionScan.objects.create(
            user=self.other,
            image_path="",
            extracted_text="other scan",
            confidence_score="80.00",
        )

        response = self.client.post(
            reverse("scans:confirm", args=[scan.id]),
            {"medicine_id": self.medicine.id},
        )

        self.assertEqual(response.status_code, 404)
        scan.refresh_from_db()
        self.assertIsNone(scan.matched_medicine)
