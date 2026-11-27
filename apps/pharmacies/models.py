from urllib.parse import quote

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

    @property
    def directions_url(self):
        """Google Maps directions to this branch.

        Coordinates are the precise destination. A row saved without usable
        coordinates falls back to its address, so the link still opens
        somewhere sensible instead of 0,0 in the Atlantic.
        """
        has_coordinates = (
            self.latitude is not None
            and self.longitude is not None
            and not (self.latitude == 0 and self.longitude == 0)
        )

        if has_coordinates:
            destination = f"{self.latitude},{self.longitude}"
        else:
            destination = self.address or self.name

        return (
            "https://www.google.com/maps/dir/?api=1&travelmode=driving&destination="
            + quote(destination, safe=",")
        )


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