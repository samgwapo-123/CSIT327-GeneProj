from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class LoginViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="alice",
            password="StrongPass!2026",
        )

    def test_valid_login_redirects_home(self):
        response = self.client.post(reverse("login:login"), {
            "username": "alice",
            "password": "StrongPass!2026",
        })
        self.assertRedirects(response, reverse("home:home"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_invalid_login_shows_error(self):
        response = self.client.post(reverse("login:login"), {
            "username": "alice",
            "password": "wrong-password",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid username or password.")

    def test_logout_requires_post(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("login:logout"))
        self.assertEqual(response.status_code, 405)

    def test_logout_post_clears_session(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("login:logout"))
        self.assertRedirects(response, reverse("login:login"))
        self.assertNotIn("_auth_user_id", self.client.session)
