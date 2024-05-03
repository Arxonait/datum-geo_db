from django.contrib.gis.geos import Polygon

from geo_db.models import Country, City, Capital


def model_country(country_id: int = None, bbox_coords: list[float] = None):
    if country_id:
        return Country.objects.filter(pk=country_id)

    filter_data = {}
    if bbox_coords:
        bbox_polygon = Polygon.from_bbox(bbox_coords)
        filter_data["coordinates__within"] = bbox_polygon

    return Country.objects.filter(**filter_data)


def model_city(city_id: int = None, bbox_coords: list[float] = None, country_id: int = None):
    if city_id:
        return City.objects.filter(pk=city_id)

    filter_data = {}
    if bbox_coords:
        bbox_polygon = Polygon.from_bbox(bbox_coords)
        filter_data["coordinates__within"] = bbox_polygon
    if country_id:
        filter_data["country_id"] = country_id

    return City.objects.filter(**filter_data)


def model_capital(capital_id: int = None, country_id: int = None, bbox_coords: list[float] = None):
    if country_id:
        return Capital.objects.filter(country_id=country_id)
    if capital_id:
        return Capital.objects.filter(pk=capital_id)

    filter_data = {}
    if bbox_coords:
        bbox_polygon = Polygon.from_bbox(bbox_coords)
        filter_data["coordinates__within"] = bbox_polygon

    return Capital.objects.filter(**filter_data)