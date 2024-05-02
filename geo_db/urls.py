from django.urls import path, include
from rest_framework import routers
from geo_db.views import *

urlpatterns = [
    path("countries/", CountryAPI.as_view()),
    path("countries/<int:country_id>", CountryAPI.as_view()),


    path("cities/", CityAPI.as_view()),
    path("cities/<int:city_id>", CityAPI.as_view()),
    path("countries/<int:country_id>/cities", CityAPI.as_view()),

    # path("countries/", ...),
    # path("countries/<int:country_id>", ...),
]
