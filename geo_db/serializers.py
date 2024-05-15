import json

from django.contrib.gis.db.models.functions import Area
from django.contrib.gis.geos import GEOSGeometry, Polygon
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from rest_framework import serializers

from geo_db.additional_modules.pagination import Paginator
from geo_db.models import Country, City, Capital, GeoModel


class GeoSerializerModel(serializers.ModelSerializer):
    area = serializers.SerializerMethodField()

    def validate_coordinates(self, value):
        try:
            polygon = GEOSGeometry(value)
        except Exception as e:
            raise ValidationError([str(e)])

        if not isinstance(polygon, Polygon):
            raise ValidationError(["geom must be a Polygon"])

        if not polygon.valid:
            raise ValidationError([f"geom is not a valid polygon: {polygon.valid_reason}"])

        for coord in polygon.coords[0]:
            if not (-180.0 <= coord[0] <= 180.0 and -90.0 <= coord[1] <= 90.0):
                raise ValidationError([
                    "Coordinates out of range: longitude must be between -180 and 180, latitude must be between -90 and 90"])
        return polygon

    def get_area(self, obj):
        area = getattr(obj, 'area', None)
        if area is None:
            return None
        return area.sq_m

    def to_representation(self, instance: GeoModel | list[GeoModel]):
        if isinstance(instance, (list, QuerySet)):
            feature_collection = {
                "type": "FeatureCollection",
                "features": [self.to_representation_single(obj) for obj in instance]
            }
            return feature_collection
        else:
            return self.to_representation_single(instance)

    def to_representation_single(self, instance):
        serialize_data = super().to_representation(instance)

        proprieties = {}
        for atr in serialize_data:
            if atr not in ["id", "coordinates"] and serialize_data[atr] is not None:
                proprieties[atr] = serialize_data[atr]

        result = {
            "type": "Feature",
            "geometry": json.loads(instance.coordinates.json),
            "id": instance.pk,
            "properties": proprieties
        }
        return result


class CountySerializer(GeoSerializerModel):
    class Meta:
        model = Country
        fields = ("id", "name", "coordinates", "area")


class CitySerializer(GeoSerializerModel):
    class Meta:
        model = City
        fields = ("id", "name", "coordinates", "area", "description", "country")


class CapitalSerializer(GeoSerializerModel):
    class Meta:
        model = Capital
        fields = ("id", "name", "coordinates", "area", "country")


class DataCollectionSerializer:
    @classmethod
    def get_feature_collection(cls, queryset, serializer, serializer_context, paginator: Paginator, query_params):
        count_data = queryset.count()
        instances = queryset[paginator.get_start():paginator.get_end()]

        feature_collection = serializer(instances, context=serializer_context).data

        if "total_area" in query_params:
            total_area = sum([obj.area.sq_m for obj in instances])
            feature_collection["total_area"] = total_area

        feature_collection.update(paginator.get_pagination_data(count_data))
        return feature_collection
