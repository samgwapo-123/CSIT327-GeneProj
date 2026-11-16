from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


class HomeViewTests(TestCase):
    def test_home_requires_login(self):
        response = self.client.get(reverse("home:home"))
        self.assertRedirects(
            response,
            reverse("login:login") + "?next=" + reverse("home:home"),
        )

    def test_home_renders_for_signed_in_user(self):
        user = User.objects.create_user(username="alice", password="StrongPass!2026")
        self.client.force_login(user)

        response = self.client.get(reverse("home:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Medicine lookup")
        self.assertContains(response, "Hello, alice")
