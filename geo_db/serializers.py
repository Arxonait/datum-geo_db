from rest_framework_gis.serializers import GeoFeatureModelSerializer, GeoModelSerializer

from geo_db.models import Country, City


class CountrySerializer(GeoModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'
        geo_field = "coordinates"


class CitySerializer(GeoModelSerializer):
    class Meta:
        model = City
        fields = '__all__'
        geo_field = "coordinates"
