import geojson
from django.db.models import Model
from rest_framework import serializers
from rest_framework.request import Request

from geo_db.models import Country, City, Capital


class GeoSerializerModel(serializers.ModelSerializer):
    def get_fields(self):
        fields = super().get_fields()
        request: Request = self.context.get("request")
        if request is None:
            fields.pop("area")  # todo
            return fields

        if "area" not in request.query_params:
            fields.pop("area")
        return fields

    def to_representation(self, instance):
        if isinstance(instance, list):
            feature_collection = geojson.FeatureCollection([self.to_representation_single(obj) for obj in instance])
            return feature_collection
        else:
            return self.to_representation_single(instance)

    def to_representation_single(self, instance):
        target_fields = self.get_fields()

        properties = {}
        for target_field in target_fields:
            if target_field not in (self.Meta.id_field, self.Meta.geo_field):
                try:
                    value = instance.__getattribute__(target_field)
                    if isinstance(value, Model):
                        value = value.id
                    properties[target_field] = value
                except AttributeError as e:
                    continue

        cords = geojson.Polygon(instance.coordinates.coords[0])

        result = geojson.Feature(id=instance.pk, geometry=cords, properties=properties)
        return result


class CountySerializer(GeoSerializerModel):
    class Meta:
        model = Country
        fields = ("id", "name", "coordinates", "area")
        id_field = "id"
        geo_field = "coordinates"


class CitySerializer(GeoSerializerModel):
    class Meta:
        model = City
        fields = ("id", "name", "coordinates", "area", "description", "country")
        id_field = "id"
        geo_field = "coordinates"


class CapitalSerializer(GeoSerializerModel):
    class Meta:
        model = Capital
        fields = ("id", "name", "coordinates", "area", "country")
        id_field = "id"
        geo_field = "coordinates"


class DataCollectionSerializer:
    @classmethod
    def get_feature_collection(cls, queryset, serializer, serializer_context, paginator, query_params):
        count_data = queryset.count()
        data = queryset[paginator.get_start():paginator.get_end()]
        feature_collection = serializer(list(queryset), context=serializer_context).data

        if query_params.get("total_area"):  # todo
            total_area = sum([obj.area for obj in data])
            feature_collection["total_area"] = total_area

        feature_collection.update(paginator.get_pagination_data(count_data))
        return feature_collection
