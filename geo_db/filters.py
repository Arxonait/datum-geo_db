import django_filters
from django.contrib.gis.geos import Polygon
from rest_framework.exceptions import ValidationError

from geo_db.additional_modules.validation import parse_valid_bbox
from geo_db.models import Country, City, Capital


class BaseGeoFilter(django_filters.FilterSet):
    bbox = django_filters.Filter(method='filter_bbox')

    def filter_bbox(self, queryset, name, *args, **kwargs):
        try:
            bbox_coords = parse_valid_bbox(self.data.get(name))
        except Exception as e:
            raise ValidationError({"detail": e.args[0]})

        bbox_polygon = Polygon.from_bbox(bbox_coords)
        queryset = queryset.filter(coordinates__within=bbox_polygon)
        return queryset


class CountryFilter(BaseGeoFilter):
    class Meta:
        model = Country
        fields = ['bbox']


class CityFilter(BaseGeoFilter):
    class Meta:
        model = City
        fields = ['bbox']


class CapitalFilter(BaseGeoFilter):
    class Meta:
        model = Capital
        fields = ['bbox']
