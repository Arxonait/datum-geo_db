from django.db.models import Model
from rest_framework_gis.serializers import GeoFeatureModelSerializer, GeoModelSerializer
from rest_framework import serializers

from geo_db.models import Country, City, GeoModel, Capital
import geojson

from geo_db.mvc_view import TypeGeoOutput


class BaseGeoSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        self.add_fields = kwargs.pop('add_fields', set())
        self.type_geo_output: TypeGeoOutput = kwargs.pop("type_geo_output", TypeGeoOutput.get_default())
        super().__init__(*args, **kwargs)

    class Meta:
        type = None
        fields = None
        geo_field = None
        id_field = None
        remove_fields = None

    def to_representation(self, instance: Country):
        target_fields = (set(self.Meta.fields) - self.Meta.remove_fields) | self.add_fields

        properties = {}
        for target_field in target_fields:
            if target_field not in (self.Meta.id_field, self.Meta.geo_field):
                value = instance.__getattribute__(target_field)
                if isinstance(value, Model):
                    value = value.id
                properties[target_field] = value

        cords = geojson.Polygon(instance.coordinates.coords[0])

        if self.type_geo_output == TypeGeoOutput.feature:
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
        remove_fields = {"area"}
        id_field = "id"
        geo_field = "coordinates"
        type = "country"


class CitySerializer(BaseGeoSerializer):
    class Meta:
        model = City
        fields = ("id", "name", "coordinates", "area", "description", "country")
        remove_fields = {"area"}
        id_field = "id"
        geo_field = "coordinates"
        type = "city"


class CapitalSerializer(BaseGeoSerializer):
    class Meta:
        model = Capital
        fields = ("id", "name", "coordinates", "area", "country")
        remove_fields = {"area"}
        id_field = "id"
        geo_field = "coordinates"
        type = "capital"
