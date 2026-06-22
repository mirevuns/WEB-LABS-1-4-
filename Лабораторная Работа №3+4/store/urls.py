from django.urls import path

from . import views

urlpatterns = [
    path("carts/", views.carts_list, name="carts_list"),
]

