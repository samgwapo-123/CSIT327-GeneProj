import os
import shutil
import tempfile
import unittest
from decimal import Decimal
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from django.apps import apps as django_apps
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .matching import find_best_match, find_best_match_in_text, match_status
from .models import PrescriptionScan
from .ocr import extract_text, ocr_installed


def build_prescription_image(lines, size=(900, 320), font_size=34):
    """Draw a printable prescription label and return PNG bytes."""
    image = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        font = ImageFont.load_default(size=font_size)

    y = 30
    for line in lines:
        draw.text((40, y), line, fill="black", font=font)
        y += int(font_size * 1.5)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


class ExtractTextTests(SimpleTestCase):
    def test_missing_file_returns_empty_string(self):
        self.assertEqual(extract_text("C:/does/not/exist.png"), "")

    @unittest.skipUnless(ocr_installed(), "rapidocr is not installed")
    def test_reads_a_printed_label(self):
        contents = build_prescription_image([
            "DR. MARIA SANTOS",
            "Coumadin 5 mg tablet",
            "Take one tablet daily",
        ])

        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "prescription.png")
            with open(path, "wb") as handle:
                handle.write(contents)

            text = extract_text(path)

        self.assertIn("Coumadin", text)
        self.assertIn("tablet", text.lower())


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


class OcrTextMatchingTests(TestCase):
    """OCR output is a whole prescription, not a single typed name."""

    def setUp(self):
        Medicine = django_apps.get_model("medicines", "Medicine")
        self.coumadin = Medicine.objects.create(
            brand_name="Coumadin",
            generic_name="Warfarin sodium",
            dosage="5 mg tablet",
            manufacturer="Sample Pharma",
            mdrp_price="30.00",
        )
        self.biogesic = Medicine.objects.create(
            brand_name="Biogesic",
            generic_name="Paracetamol",
            dosage="500 mg tablet",
            manufacturer="Unilab",
            mdrp_price="5.00",
        )

    def test_brand_name_inside_a_prescription_is_found(self):
        text = (
            "DR. MARIA SANTOS\n"
            "Cebu City\n"
            "Rx:\n"
            "Coumadin 5 mg tablet\n"
            "Take one tablet daily\n"
            "Refill: 30 days"
        )

        medicine, confidence, snippet = find_best_match_in_text(text)

        self.assertEqual(medicine, self.coumadin)
        self.assertGreater(confidence, 90)
        self.assertEqual(snippet, "coumadin")

    def test_generic_name_is_found_too(self):
        medicine, confidence, snippet = find_best_match_in_text(
            "Paracetamol 500 mg as needed"
        )

        self.assertEqual(medicine, self.biogesic)
        self.assertGreater(confidence, 90)
        self.assertEqual(snippet, "paracetamol")

    def test_unrelated_text_stays_below_the_confirm_threshold(self):
        medicine, confidence, snippet = find_best_match_in_text(
            "Clinic hours: Monday to Friday"
        )

        self.assertLess(confidence, 70)
        self.assertEqual(snippet, "")

    def test_empty_text_returns_no_match(self):
        medicine, confidence, snippet = find_best_match_in_text("")

        self.assertIsNone(medicine)
        self.assertEqual(confidence, 0.0)
        self.assertEqual(snippet, "")


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

    def valid_upload(self, name="prescription.png", size=(600, 300), text=None):
        """A real PNG. Pillow checks the signature, so bytes must be genuine."""
        image = Image.new("RGB", size, "white")

        if text:
            draw = ImageDraw.Draw(image)
            try:
                font = ImageFont.truetype("arial.ttf", 34)
            except OSError:
                font = ImageFont.load_default(size=34)
            draw.text((40, 40), text, fill="black", font=font)

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")

    def corrupt_upload(self, name="prescription.png"):
        """A file that claims to be a PNG but is not one."""
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

    def test_unreadable_image_asks_for_a_clearer_photo(self):
        # A real but blank page: nothing to read, so the message is honest.
        response = self.client.post(reverse("scans:scan"), {
            "medicine_name": "",
            "image": self.valid_upload(),
        })

        self.assertContains(response, "no readable text was found")

        scan = PrescriptionScan.objects.get(user=self.user)
        self.assertEqual(scan.extracted_text, "")
        self.assertEqual(scan.confidence_score, Decimal("0.00"))
        self.assertIsNone(scan.matched_medicine)

    def test_corrupt_image_is_rejected_before_it_is_stored(self):
        response = self.client.post(reverse("scans:scan"), {
            "medicine_name": "Biogesic",
            "image": self.corrupt_upload(),
        })

        self.assertContains(response, "could not be read as an image")
        self.assertFalse(PrescriptionScan.objects.filter(user=self.user).exists())

        stored = os.path.join(self.media_root, "scans")
        self.assertFalse(os.path.isdir(stored) and os.listdir(stored))

    @unittest.skipUnless(ocr_installed(), "rapidocr is not installed")
    def test_uploaded_label_is_read_without_typing_a_name(self):
        upload = SimpleUploadedFile(
            "label.png",
            build_prescription_image([
                "DR. MARIA SANTOS",
                "Rx:",
                "Biogesic 500 mg tablet",
                "Take one tablet every six hours",
            ]),
            content_type="image/png",
        )

        response = self.client.post(reverse("scans:scan"), {
            "medicine_name": "",
            "image": upload,
        })

        self.assertContains(response, "Match found")
        self.assertContains(response, "Text read from the image")

        scan = PrescriptionScan.objects.get(user=self.user)
        self.assertIn("Biogesic", scan.extracted_text)
        self.assertEqual(scan.matched_medicine, self.medicine)
        self.assertGreater(scan.confidence_score, Decimal("90"))

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
