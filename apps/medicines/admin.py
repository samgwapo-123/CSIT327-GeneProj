from django.contrib import admin
from .models import Medicine, GenericAlternative

admin.site.register(Medicine)
admin.site.register(GenericAlternative)