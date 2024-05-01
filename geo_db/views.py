import geojson
from django.contrib.gis.geos import Polygon
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from geo_db.models import Country, City
from geo_db.mvc_view import output_geo_json_format
from geo_db.pagination import pagination
from geo_db.serializers import CountrySerializer, CitySerializer


class CountryAPI(APIView):
    @pagination
    def get(self, request: Request, country_id=None, limit=None, offset=None):
        """
        query_params: \n
        limit, offset \n
        area m^2 \n
        bbox x_min y_min x_max y_max \n
        type_geo_output ['simple', 'feature'] default simple
        """

        filter_data = {}
        if country_id is not None:
            limit = 10
            offset = 0
            filter_data["pk"] = country_id

        if request.query_params.get("bbox"):
            bbox_coords = request.query_params.get("bbox").split()
            bbox_coords = [float(coord) for coord in bbox_coords]

            if len(bbox_coords) != 4:
                return Response(data={"detail": "bbox required format x_min y_min x_max y_max"},
                                status=status.HTTP_404_NOT_FOUND)

            bbox_polygon = Polygon.from_bbox(bbox_coords)
            filter_data["coordinates__within"] = bbox_polygon

        countries = Country.objects.filter(**filter_data)
        count_data = len(countries)

        if country_id is not None and count_data == 0:
            return Response(data={"detail": "country not found"}, status=status.HTTP_404_NOT_FOUND)

        add_fields = set()
        if request.query_params.get("area"):
            add_fields.add("area")

        countries = countries[offset:offset + limit]

        type_geo_output = request.query_params.get("type_geo_output", "simple")
        try:
            result_data = output_geo_json_format(type_geo_output, CountrySerializer, countries, count_data, add_fields)
        except Exception as e:
            return Response(data={"detail": e.args[0]}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data=result_data)

    def post(self, request: Request):
        country = CountrySerializer(data=request.data)
        country.is_valid(raise_exception=True)
        country.save()
        return Response(data=country.data, status=status.HTTP_201_CREATED)

    def patch(self, request, country_id=None, partial=True):
        if country_id is None:
            return Response(data={"detail": "country id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            country = Country.objects.get()
        except:
            return Response(data={"detail": "country not found"}, status=status.HTTP_404_NOT_FOUND)

        country_data_update = CountrySerializer(data=request.data, instance=country, partial=partial)
        country_data_update.is_valid(raise_exception=True)
        country_data_update.save()
        return Response(data=country.data, status=status.HTTP_200_OK)

    def put(self, request, country_id=None):
        return self.patch(request, country_id, partial=False)

    def delete(self, request: Request, country_id):
        if country_id is None:
            return Response(data={"detail": "country id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            country = Country.objects.get()
        except:
            return Response(data={"detail": "country not found"}, status=status.HTTP_404_NOT_FOUND)

        country.delete()

        return Response({"detail": f"delete object {country_id}"})


class CityAPI(APIView):
    @pagination
    def get(self, request: Request, city_id=None, limit=None, offset=None):
        """
        query_params: \n
        limit, offset \n
        area m^2 \n
        bbox x_min y_min x_max y_max \n
        type_geo_output ['simple', 'feature'] default simple
        """

        filter_data = {}
        if city_id is not None:
            limit = 10
            offset = 0
            filter_data["pk"] = city_id

        if request.query_params.get("bbox"):
            bbox_coords = request.query_params.get("bbox").split()
            bbox_coords = [float(coord) for coord in bbox_coords]

            if len(bbox_coords) != 4:
                return Response(data={"detail": "bbox required format x_min y_min x_max y_max"},
                                status=status.HTTP_404_NOT_FOUND)

            bbox_polygon = Polygon.from_bbox(bbox_coords)
            filter_data["coordinates__within"] = bbox_polygon

        cities = City.objects.filter(**filter_data)
        count_data = len(cities)

        if city_id is not None and count_data == 0:
            return Response(data={"detail": "city not found"}, status=status.HTTP_404_NOT_FOUND)

        add_fields = set()
        if request.query_params.get("area"):
            add_fields.add("area")

        cities = cities[offset:offset + limit]

        type_geo_output = request.query_params.get("type_geo_output", "simple")
        try:
            result_data = output_geo_json_format(type_geo_output, CitySerializer, cities, count_data, add_fields)
        except Exception as e:
            return Response(data={"detail": e.args[0]}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data=result_data)

    def post(self, request: Request):
        city = CitySerializer(data=request.data)
        city.is_valid(raise_exception=True)

        try:
            city.save()
        except Exception as e:
            return Response({"detail": f"error: {e.args}"}, status=status.HTTP_404_NOT_FOUND)

        return Response(data=city.data, status=status.HTTP_201_CREATED)

    def patch(self, request, city_id=None, partial=True):
        if city_id is None:
            return Response({"detail": "city id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            city = City.objects.get()
        except:
            return Response({"detail": "city not found"}, status=status.HTTP_404_NOT_FOUND)

        city_data_update = CitySerializer(data=request.data, instance=city, partial=partial)
        city_data_update.is_valid(raise_exception=True)
        city_data_update.save()
        return Response(data=city.data, status=status.HTTP_200_OK)

    def put(self, request, city_id=None):
        return self.patch(request, city_id, partial=False)

    def delete(self, request: Request, city_id):
        if city_id is None:
            return Response({"detail": "city id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            city = City.objects.get()
        except:
            return Response({"detail": "city not found"}, status=status.HTTP_404_NOT_FOUND)

        city.delete()

        return Response({"detail": f"delete object {city_id}"})
