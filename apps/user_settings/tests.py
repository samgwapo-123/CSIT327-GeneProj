from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import UserSettings


class SettingsViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="StrongPass!2026")

    def test_settings_requires_login(self):
        response = self.client.get(reverse("user_settings:settings"))
        self.assertEqual(response.status_code, 302)

    def test_settings_update_saves_both_toggles(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("user_settings:settings"), {
            "dark_mode": "on",
            "email_notifications": "on",
        })

        self.assertRedirects(response, reverse("user_settings:settings"))
        settings_obj = UserSettings.objects.get(user=self.user)
        self.assertTrue(settings_obj.dark_mode)
        self.assertTrue(settings_obj.email_notifications)

    def test_dark_mode_adds_body_class_on_home(self):
        self.client.force_login(self.user)
        self.client.post(reverse("user_settings:settings"), {"dark_mode": "on"})

        response = self.client.get(reverse("home:home"))

        self.assertContains(response, "dark-mode")

    def test_settings_page_says_email_is_not_implemented(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("user_settings:settings"))
        self.assertContains(response, "Email delivery is not implemented")
