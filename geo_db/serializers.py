import json

from django.contrib.gis.db.models.functions import Area
from django.contrib.gis.geos import GEOSGeometry, Polygon
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from rest_framework import serializers

from geo_db.models import Country, City, Capital


class GeoSerializerModel(serializers.ModelSerializer):
    area = serializers.SerializerMethodField()

    def __init__(self, *args, single=True, **kwargs):
        super().__init__(*args, **kwargs)
        self.single = single

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

    def change_queryset_serializers_context(self, queryset):
        context = self.context
        if "area" in context:
            queryset = queryset.annotate(area=Area('coordinates'))

        return queryset

    def to_representation(self, queryset: QuerySet):
        if not isinstance(queryset, QuerySet) and self.single == True:
            return self.to_representation_single(queryset)

        instances = self.change_queryset_serializers_context(queryset)
        if not self.single:
            feature_collection = {
                "type": "FeatureCollection",
                "features": [self.to_representation_single(obj) for obj in instances]
            }
            return feature_collection
        else:
            instance = instances[0]
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
    def get_feature_collection(cls, queryset, serializer, serializer_context, paginator, query_params):
        count_data = queryset.count()
        data = queryset[paginator.get_start():paginator.get_end()]
        feature_collection = serializer(queryset, context=serializer_context, single=False).data

        if query_params.get("total_area"):  # todo
            total_area = sum([obj.area for obj in data])
            feature_collection["total_area"] = total_area

        feature_collection.update(paginator.get_pagination_data(count_data))
        return feature_collection
