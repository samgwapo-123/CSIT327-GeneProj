from django.contrib.auth.models import User
from django.db import models


class UserSettings(models.Model):
    """ERD entity: user_settings (1:1 with auth_user)"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="settings")
    dark_mode = models.BooleanField(default=False)
    email_notifications = models.BooleanField(default=True)

    class Meta:
        db_table = "user_settings"

    def __str__(self):
        return f"Settings for {self.user.username}"