from django.urls import path

from .views import pharmacy_list_view

app_name = "pharmacies"

urlpatterns = [
    path("", pharmacy_list_view, name="list"),
]
