from django.db import models


class Medicine(models.Model):
    """ERD entity: medicines (brand-name medicine)"""
    brand_name = models.CharField(max_length=150)
    generic_name = models.CharField(max_length=150)
    dosage = models.CharField(max_length=50)
    manufacturer = models.CharField(max_length=150)
    rx_required = models.BooleanField(default=False)
    nti_warning = models.BooleanField(default=False)
    mdrp_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "medicines"

    def __str__(self):
        return self.brand_name


class GenericAlternative(models.Model):
    """ERD entity: generic_alternatives (M:1 with medicines)"""
    medicine = models.ForeignKey(
        Medicine, on_delete=models.CASCADE, related_name="generic_alternatives"
    )
    generic_brand_name = models.CharField(max_length=150)
    manufacturer = models.CharField(max_length=150)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "generic_alternatives"

    def __str__(self):
        return f"{self.generic_brand_name} (for {self.medicine.brand_name})"