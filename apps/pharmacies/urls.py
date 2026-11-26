from django.urls import path

from .views import pharmacy_list_view, restock_watch_view, stock_ledger_view

app_name = "pharmacies"

urlpatterns = [
    path("", pharmacy_list_view, name="list"),
    path("stock/", stock_ledger_view, name="stock"),
    path("restock/", restock_watch_view, name="restock"),
]
