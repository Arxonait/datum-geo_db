from rest_framework_gis.serializers import GeoFeatureModelSerializer, GeoModelSerializer
from rest_framework import serializers

from geo_db.models import Country, City
import geojson


class BaseGeoSerializer(serializers.ModelSerializer):
    area = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        self.remove_fields = kwargs.pop('remove_fields', set())
        type_geo_output = kwargs.pop("type_geo_output", "simple")
        if type_geo_output in ("simple", "feature"):
            self.type_geo_output = type_geo_output
        else:
            self.type_geo_output = "simple"
        super().__init__(*args, **kwargs)

    class Meta:
        type = None
        fields = None
        geo_field = None
        id_field = None

    def to_representation(self, instance: Country):
        target_fields = set(self.Meta.fields) - self.remove_fields

        properties = {}
        for target_field in target_fields:
            if target_field not in (self.Meta.id_field, self.Meta.geo_field):
                properties[target_field] = instance.__getattribute__(target_field)

        cords = geojson.Polygon(instance.coordinates.coords[0])

        if self.type_geo_output == "feature":
            result = geojson.Feature(id=instance.pk, geometry=cords, properties=properties)
        else:
            attributes = {
                "coordinates": cords
            }
            attributes.update(properties)
            result = {
                "id": instance.pk,
                "type": self.Meta.type,
                "attributes": attributes
            }
        return result


class CountrySerializer(BaseGeoSerializer):
    class Meta:
        model = Country
        fields = ("id", "name", "coordinates", "area")
        id_field = "id"
        geo_field = "coordinates"
        type = "country"


class CitySerializer(BaseGeoSerializer):
    class Meta:
        model = City
        fields = '__all__'
        geo_field = "coordinates"
