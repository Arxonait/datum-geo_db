from django.contrib.gis import geos
from django.contrib.gis.gdal import SpatialReference, CoordTransform
from django.contrib.gis.geos import GEOSGeometry, Polygon, GEOSException
from osgeo import ogr
from pyproj import Transformer
from rest_framework import status
from rest_framework.request import Request
from rest_framework.views import APIView

from geo_db.MyResponse import MyResponse
from geo_db.models import Country, City
from geo_db.pagination import pagination
from geo_db.serializers import CountrySerializer


class CountryAPI(APIView):
    @pagination
    def get(self, request: Request, country_id=None, limit=None, offset=None):
        """
        query_params:
        limit, offset
        area
        bbox
        """

        filter_data = {}
        if country_id is not None:
            limit = 0
            offset = 0
            filter_data["pk"] = country_id
        if request.query_params.get("bbox"):
            pass  # todo

        countries = Country.objects.filter(**filter_data)
        count_data = len(countries)

        if country_id is not None and count_data == 0:
            return MyResponse(detail="Country not found", status_code=status.HTTP_404_NOT_FOUND).to_response_api()

        if request.query_params.get("area"):
            for i in countries:
                print("Площадь полигона:", i.get_area(), "квадратных метров")

        countries = countries[offset:offset+limit]

        response = MyResponse(data=CountrySerializer(countries, many=True).data, count_data=count_data)
        return response.to_response_api()

    def post(self, request: Request):
        country = CountrySerializer(data=request.data)
        country.is_valid(raise_exception=True)
        country.save()
        response = MyResponse(data=country.data)
        return response.to_response_api()

    def patch(self, request, country_id=None, partial=True):
        if country_id is None:
            return MyResponse(detail="Country id is required", status_code=status.HTTP_400_BAD_REQUEST).to_response_api()

        try:
            country = Country.objects.get(pk=country_id)
        except:
            return MyResponse(detail="Country not found", status_code=status.HTTP_404_NOT_FOUND).to_response_api()

        country_data_update = CountrySerializer(data=request.data, instance=country, partial=partial)
        country_data_update.is_valid(raise_exception=True)
        country_data_update.save()
        response = MyResponse(data=country_data_update.data)
        return response.to_response_api()

    def put(self, request, country_id=None):
        return self.patch(request, country_id, partial=False)

    def delete(self, request: Request, country_id):
        if country_id is None:
            return MyResponse(detail="Country id is required", status_code=status.HTTP_400_BAD_REQUEST).to_response_api()

        try:
            country = Country.objects.get(pk=country_id)
        except:
            return MyResponse(detail="Country not found", status_code=status.HTTP_404_NOT_FOUND).to_response_api()

        country.delete()

        return MyResponse(detail=f"delete object {country_id}").to_response_api()


class CityAPI(APIView):
    def get(self):
        ...

    def post(self, request: Request):
        city = CountrySerializer(data=request.data)
        city.is_valid(raise_exception=True)
        city.save()
        response = MyResponse(data=city.data)
        return response.to_response_api()

    def patch(self, request, city_id=None, partial=True):
        if city_id is None:
            return MyResponse(detail="city id is required", status_code=status.HTTP_400_BAD_REQUEST).to_response_api()

        try:
            city = City.objects.get(pk=city_id)
        except:
            return MyResponse(detail="city not found", status_code=status.HTTP_404_NOT_FOUND).to_response_api()

        city_data_update = CountrySerializer(data=request.data, instance=city, partial=partial)
        city_data_update.is_valid(raise_exception=True)
        city_data_update.save()
        response = MyResponse(data=city_data_update.data)
        return response.to_response_api()

    def put(self, request, city_id=None):
        return self.patch(request, city_id, partial=False)

    def delete(self, request: Request, city_id):
        if city_id is None:
            return MyResponse(detail="city id is required", status_code=status.HTTP_400_BAD_REQUEST).to_response_api()

        try:
            city = City.objects.get(pk=city_id)
        except:
            return MyResponse(detail="city not found", status_code=status.HTTP_404_NOT_FOUND).to_response_api()

        city.delete()

        return MyResponse(detail=f"delete object {city_id}").to_response_api()
