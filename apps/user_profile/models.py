from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    """ERD entity: profiles (1:1 with auth_user)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True)

    class Meta:
        db_table = "profiles"

    def __str__(self):
        return self.user.username