from django.db import models


class Pharmacy(models.Model):
    """ERD entity: pharmacies"""
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    contact_number = models.CharField(max_length=20, blank=True)
    operating_hours = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "pharmacies"

    def __str__(self):
        return self.name


class PharmacyStock(models.Model):
    """ERD entity: pharmacy_stock (junction: pharmacies M:M medicines)"""
    pharmacy = models.ForeignKey(
        Pharmacy, on_delete=models.CASCADE, related_name="stock_items"
    )
    # String reference ("app_label.Model") avoids importing another feature's code
    medicine = models.ForeignKey(
        "medicines.Medicine", on_delete=models.CASCADE, related_name="stock_items"
    )
    in_stock = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pharmacy_stock"

    def __str__(self):
        return f"{self.medicine} @ {self.pharmacy}"