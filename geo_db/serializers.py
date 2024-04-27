from rest_framework_gis.serializers import GeoFeatureModelSerializer, GeoModelSerializer

from geo_db.models import Country


class CountrySerializer(GeoModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'
        geo_field = "coordinates"
