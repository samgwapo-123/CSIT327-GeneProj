from django.contrib.auth.models import User
from django.db import models


class PrescriptionScan(models.Model):
    """ERD entity: prescription_scans (OCR scan history)"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="prescription_scans"
    )
    # Nullable FK: a scan may not match any medicine (0..M on the scan side)
    matched_medicine = models.ForeignKey(
        "medicines.Medicine",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prescription_scans",
    )
    image_path = models.CharField(max_length=255)
    extracted_text = models.TextField(blank=True)
    confidence_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "prescription_scans"

    def __str__(self):
        return f"Scan #{self.pk} by {self.user.username}"