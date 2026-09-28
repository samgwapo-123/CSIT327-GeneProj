from django.contrib import admin
from .models import Pharmacy, PharmacyStock

admin.site.register(Pharmacy)
admin.site.register(PharmacyStock)