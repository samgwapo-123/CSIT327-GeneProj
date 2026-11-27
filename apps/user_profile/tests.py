import os
import shutil
import tempfile
from io import BytesIO

from PIL import Image

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import Profile


def png_upload(name="me.png", size=(120, 120), colour=(80, 160, 200)):
    """A real PNG so ImageField/Pillow validation passes."""
    image = Image.new("RGB", size, colour)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


class ProfileViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="StrongPass!2026")

        self.media_root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.media_root, True)
        self.media_override = override_settings(MEDIA_ROOT=self.media_root)
        self.media_override.enable()
        self.addCleanup(self.media_override.disable)

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

    def test_avatar_upload_is_stored_on_disk(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("user_profile:profile"), {
            "full_name": "Alice Cruz",
            "bio": "",
            "avatar": png_upload(),
        })

        self.assertRedirects(response, reverse("user_profile:profile"))

        profile = Profile.objects.get(user=self.user)
        self.assertTrue(profile.avatar.name.startswith("avatars/"))
        self.assertTrue(os.path.exists(profile.avatar.path))

    def test_avatar_appears_in_navigation_and_survives_reload(self):
        self.client.force_login(self.user)
        self.client.post(reverse("user_profile:profile"), {"avatar": png_upload()})

        profile = Profile.objects.get(user=self.user)
        avatar_url = profile.avatar.url

        # A fresh request must read the stored path, not an in-memory upload.
        response = self.client.get(reverse("home:home"))

        self.assertContains(response, avatar_url)
        self.assertContains(response, 'aria-label="Your profile, alice"')

    def test_avatar_survives_logout_and_login(self):
        self.client.force_login(self.user)
        self.client.post(reverse("user_profile:profile"), {"avatar": png_upload()})
        avatar_url = Profile.objects.get(user=self.user).avatar.url

        self.client.post(reverse("login:logout"))
        self.client.post(reverse("login:login"), {
            "username": "alice",
            "password": "StrongPass!2026",
        })

        response = self.client.get(reverse("user_profile:profile"))
        self.assertContains(response, avatar_url)

    def test_replacing_an_avatar_deletes_the_old_file(self):
        self.client.force_login(self.user)

        self.client.post(reverse("user_profile:profile"), {"avatar": png_upload("first.png")})
        first = Profile.objects.get(user=self.user).avatar
        first_path = first.path

        self.client.post(reverse("user_profile:profile"), {"avatar": png_upload("second.png")})

        profile = Profile.objects.get(user=self.user)
        self.assertNotEqual(profile.avatar.name, first.name)
        self.assertFalse(os.path.exists(first_path))
        self.assertTrue(os.path.exists(profile.avatar.path))

    def test_remove_avatar_clears_the_field_and_the_file(self):
        self.client.force_login(self.user)
        self.client.post(reverse("user_profile:profile"), {"avatar": png_upload()})

        stored = Profile.objects.get(user=self.user).avatar
        stored_path = stored.path

        response = self.client.post(reverse("user_profile:profile"), {
            "remove_avatar": "on",
        })

        self.assertRedirects(response, reverse("user_profile:profile"))
        profile = Profile.objects.get(user=self.user)
        self.assertFalse(profile.avatar)
        self.assertFalse(os.path.exists(stored_path))

    def test_non_image_upload_is_rejected_without_saving_fields(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("user_profile:profile"), {
            "full_name": "Should Not Save",
            "avatar": SimpleUploadedFile(
                "notes.png", b"this is not an image", content_type="image/png"
            ),
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "could not be read as an image")
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.full_name, "")
        self.assertFalse(profile.avatar)

    def test_oversized_avatar_is_rejected(self):
        self.client.force_login(self.user)

        big = SimpleUploadedFile(
            "big.png",
            b"x" * (2 * 1024 * 1024 + 1),
            content_type="image/png",
        )
        response = self.client.post(reverse("user_profile:profile"), {"avatar": big})

        self.assertContains(response, "larger than 2 MB")
        self.assertFalse(Profile.objects.get(user=self.user).avatar)

    def test_wrong_file_type_is_rejected(self):
        self.client.force_login(self.user)

        response = self.client.post(reverse("user_profile:profile"), {
            "avatar": SimpleUploadedFile("photo.gif", b"GIF89a", content_type="image/gif"),
        })

        self.assertContains(response, "Choose a JPG, PNG, or WebP image.")
        self.assertFalse(Profile.objects.get(user=self.user).avatar)


class NavigationProfileLinkTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="StrongPass!2026")
        self.client.force_login(self.user)

    def test_profile_text_link_is_gone(self):
        response = self.client.get(reverse("home:home"))

        self.assertNotContains(response, '>Profile</a>')

    def test_avatar_links_to_the_profile_page(self):
        response = self.client.get(reverse("home:home"))

        self.assertContains(response, 'href="{}"'.format(reverse("user_profile:profile")))
        self.assertContains(response, 'aria-label="Your profile, alice"')

    def test_avatar_shows_the_initial_without_a_photo(self):
        response = self.client.get(reverse("home:home"))

        self.assertContains(response, "genrx-avatar")
        self.assertNotContains(response, "/media/avatars/")
