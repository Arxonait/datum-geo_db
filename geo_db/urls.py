from django.urls import path, include
from rest_framework import routers
from geo_db.views import *

router = routers.SimpleRouter()
router.register(r"countries", CountryViewSet,  basename='country')
router.register(r"cities", CityViewSet)
router.register(r"capitals", CapitalViewSet)

urlpatterns = [
    path("", include(router.urls)),
]
