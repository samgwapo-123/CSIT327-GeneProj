from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Profile


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="StrongPass!2026")

    def test_profile_requires_login(self):
        response = self.client.get(reverse("user_profile:profile"))
        self.assertEqual(response.status_code, 302)

    def test_profile_update_saves_fields(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("user_profile:profile"), {
            "full_name": "Alice Cruz",
            "bio": "Allergic to penicillin.",
        })

        self.assertRedirects(response, reverse("user_profile:profile"))
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.full_name, "Alice Cruz")
        self.assertEqual(profile.bio, "Allergic to penicillin.")
