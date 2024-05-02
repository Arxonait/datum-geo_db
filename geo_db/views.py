import base64
import datetime
import os

from django.core.files.base import ContentFile
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from geo_db.decorators import get_standard_query_param
from geo_db.models import Country, City, Photo
from geo_db.mvc_model import model_country, model_city
from geo_db.mvc_view import output_many_geo_json_format, output_one_geo_json_format
from geo_db.pagination import pagination
from geo_db.serializers import CountrySerializer, CitySerializer


class CountryAPI(APIView):
    @get_standard_query_param
    @pagination
    def get(self, request: Request, country_id=None, pagination_data=None, **kwargs):
        """
        query_params: \n
        limit, offset \n
        area: bool m^2 \n
        bbox x_min y_min x_max y_max \n
        type_geo_output ['simple', 'feature'] default simple
        total area: bool
        """
        limit = pagination_data["limit"]
        offset = pagination_data["offset"]
        type_geo_output = kwargs["get_params"]["type_geo_output"]

        add_fields = set()
        if request.query_params.get("area"):
            add_fields.add("area")

        if country_id is not None:
            countries = model_country(country_id=country_id)
            if len(countries) == 0:
                return Response(data={"detail": "country not found"}, status=status.HTTP_404_NOT_FOUND)
            try:
                result_data = output_one_geo_json_format(type_geo_output, CountrySerializer, countries, add_fields)
                return Response(data=result_data)
            except Exception as e:
                return Response(data={"detail": e.args[0]}, status=status.HTTP_400_BAD_REQUEST)

        # для нескольких объектов
        countries = model_country(bbox_coords=kwargs["get_params"]["bbox"])
        count_data = len(countries)

        countries = countries[offset: offset + limit]
        total_area = None
        if request.query_params.get("total_area", "false").lower() == "true":
            total_area = sum([obj.area for obj in countries])

        try:
            result_data = output_many_geo_json_format(type_geo_output, CountrySerializer, countries,
                                                      pagination_data, count_data, add_fields, total_area)
            return Response(data=result_data)
        except Exception as e:
            return Response(data={"detail": e.args[0]}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request: Request):
        country = CountrySerializer(data=request.data)
        country.is_valid(raise_exception=True)
        country.save()
        return Response(data=country.data, status=status.HTTP_201_CREATED)

    def patch(self, request, country_id=None, partial=True):
        if country_id is None:
            return Response(data={"detail": "country id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            country = Country.objects.get(pk=country_id)
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
            country = Country.objects.get(pk=country_id)
        except:
            return Response(data={"detail": "country not found"}, status=status.HTTP_404_NOT_FOUND)

        country.delete()

        return Response({"detail": f"delete object {country_id}"})


class CityAPI(APIView):
    @get_standard_query_param
    @pagination
    def get(self, request: Request, city_id=None, country_id=None, pagination_data=None, **kwargs):
        """
        query_params: \n
        limit, offset \n
        area: bool m^2 \n
        bbox x_min y_min x_max y_max \n
        type_geo_output ['simple', 'feature'] default simple
        total area: bool
        """
        limit = pagination_data["limit"]
        offset = pagination_data["offset"]
        type_geo_output = kwargs["get_params"]["type_geo_output"]

        add_fields = set()
        if request.query_params.get("area"):
            add_fields.add("area")

        if city_id is not None:
            cities = model_city(city_id=city_id)
            if len(cities) == 0:
                return Response(data={"detail": "city not found"}, status=status.HTTP_404_NOT_FOUND)
            try:
                result_data = output_one_geo_json_format(type_geo_output, CitySerializer, cities, add_fields)
                return Response(data=result_data)
            except Exception as e:
                return Response(data={"detail": e.args[0]}, status=status.HTTP_400_BAD_REQUEST)

        # для нескольких объектов
        cities = model_city(bbox_coords=kwargs["get_params"]["bbox"], country_id=country_id)
        count_data = len(cities)

        cities = cities[offset: offset + limit]
        total_area = None
        if request.query_params.get("total_area", "false").lower() == "true":
            total_area = sum([obj.area for obj in cities])

        try:
            result_data = output_many_geo_json_format(type_geo_output, CitySerializer, cities,
                                                      pagination_data, count_data, add_fields, total_area)
            return Response(data=result_data)
        except Exception as e:
            return Response(data={"detail": e.args[0]}, status=status.HTTP_400_BAD_REQUEST)

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
            city = City.objects.get(pk=city_id)
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
            city = City.objects.get(pk=city_id)
        except:
            return Response({"detail": "city not found"}, status=status.HTTP_404_NOT_FOUND)

        city.delete()

        return Response({"detail": f"delete object {city_id}"})


class ImagesCityAPI(APIView):
    def post(self, request: Request, city_id):
        os.makedirs(os.path.dirname(os.getenv("IMAGES_PATH")), exist_ok=True)

        if city_id is None:
            return Response({"detail": "city id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            city = City.objects.get(pk=city_id)
        except:
            return Response({"detail": "city not found"}, status=status.HTTP_404_NOT_FOUND)

        base64_image = request.data.get("base64_image")
        if base64_image is None:
            return Response({"detail": "base64_image is required"}, status=status.HTTP_400_BAD_REQUEST)

        photo = Photo(city=city, base64_image=base64_image)
        photo.save()
        return Response(data={"status": "created"}, status=status.HTTP_201_CREATED)