from django.db.models import Model
from rest_framework import serializers
from rest_framework.request import Request

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



class NewCountySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ("id", "name", "coordinates", "area")
        id_field = "id"
        geo_field = "coordinates"

    def get_fields(self):
        fields = super(NewCountySerializer, self).get_fields()
        request: Request = self.context.get("request")
        if request is None:
            fields.pop("area")
            return fields

        if "area" not in request.query_params:
            fields.pop("area")
        return fields

    def to_representation(self, instance):
        target_fields = self.get_fields()

        properties = {}
        for target_field in target_fields:
            if target_field not in (self.Meta.id_field, self.Meta.geo_field):
                try:
                    value = instance.__getattribute__(target_field)
                    properties[target_field] = value
                except AttributeError as e:
                    print(f"LOG --- serializers country --- {e.args[0]}")

        cords = geojson.Polygon(instance.coordinates.coords[0])

        result = geojson.Feature(id=instance.pk, geometry=cords, properties=properties)
        return result


class FeatureCollectionSerializer:
    @classmethod
    def get_feature_collection(cls, queryset, serializer, serializer_context, paginator, query_params):
        count_data = queryset.count()
        data = queryset[paginator.get_start():paginator.get_end()]
        features = [serializer(instance, context=serializer_context).data for instance in data]
        feature_collection = geojson.FeatureCollection(features)

        if query_params.get("total_area"):
            total_area = sum([obj.area for obj in data])
            feature_collection["total_area"] = total_area

        feature_collection.update(paginator.get_pagination_data(count_data))
        return feature_collection
