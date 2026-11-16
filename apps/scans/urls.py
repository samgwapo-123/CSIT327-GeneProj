from django.urls import path

from .views import confirm_match_view, history_view, scan_view

app_name = "scans"

urlpatterns = [
    path("", scan_view, name="scan"),
    path("<int:scan_id>/confirm/", confirm_match_view, name="confirm"),
    path("history/", history_view, name="history"),
]
