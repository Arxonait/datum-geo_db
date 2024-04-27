from django.urls import path, include
from rest_framework import routers
from geo_db.views import *

urlpatterns = [
    path("countries/", CountryApiView.as_view()),
    path("countries/<int:country_id>", CountryApiView.as_view()),
]
