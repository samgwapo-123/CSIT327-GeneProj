from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class RegisterViewTests(TestCase):
    def valid_payload(self, **overrides):
        payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "StrongPass!2026",
            "confirm_password": "StrongPass!2026",
        }
        payload.update(overrides)
        return payload

    def test_register_creates_user(self):
        response = self.client.post(reverse("register:register"), self.valid_payload())
        self.assertRedirects(response, reverse("login:login"))
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_confirm_password_mismatch_is_rejected(self):
        response = self.client.post(reverse("register:register"), self.valid_payload(
            confirm_password="DifferentPass!2026",
        ))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwords do not match.")
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_weak_password_is_rejected(self):
        response = self.client.post(reverse("register:register"), self.valid_payload(
            password="12345",
            confirm_password="12345",
        ))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "too short")
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_duplicate_username_is_rejected(self):
        User.objects.create_user(username="newuser", password="StrongPass!2026")
        response = self.client.post(reverse("register:register"), self.valid_payload())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Username already exists.")
        self.assertEqual(User.objects.filter(username="newuser").count(), 1)

    def test_both_password_fields_have_reveal_buttons(self):
        response = self.client.get(reverse("register:register"))
        html = response.content.decode()

        self.assertEqual(html.count("data-password-toggle"), 2)
        self.assertContains(response, 'aria-controls="password"')
        self.assertContains(response, 'aria-controls="confirm_password"')
        self.assertContains(response, "js/shared/password-toggle.js")
