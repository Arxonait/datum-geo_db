from django.urls import path, include
from rest_framework import routers
from geo_db.views import *

router = routers.SimpleRouter()
router.register(r"countries", CountryViewSet)

urlpatterns = [
    # path("countries/", CountryAPI.as_view()),
    # path("countries/<int:country_id>", CountryAPI.as_view()),
    path("", include(router.urls), name="countries"),


    path("cities/", CityAPI.as_view()),
    path("cities/<int:city_id>", CityAPI.as_view()),
    # path("countries/<int:country_id>/cities", CityAPI.as_view()),

    path("cities/<int:city_id>/images", ImagesCityAPI.as_view()),
    path("cities/<int:city_id>/images/<int:num_image>", ImagesCityAPI.as_view()),

    path("capitals/", CapitalAPI.as_view()),
    path("capitals/<int:capital_id>", CapitalAPI.as_view()),
    path("countries/<int:country_id>/capital", CapitalAPI.as_view())
]
