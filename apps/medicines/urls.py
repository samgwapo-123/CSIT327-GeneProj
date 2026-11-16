from django.urls import path

from .views import generics_view, search_view

app_name = "medicines"

urlpatterns = [
    path("search/", search_view, name="search"),
    path("<int:medicine_id>/generics/", generics_view, name="generics"),
]
