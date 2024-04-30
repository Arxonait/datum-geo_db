import geojson
from django.contrib.gis.geos import Polygon
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from geo_db.MyResponse import MyResponse
from geo_db.models import Country, City
from geo_db.pagination import pagination
from geo_db.serializers import CountrySerializer


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

        remove_fields = set()
        if not request.query_params.get("area"):
            remove_fields.add("area")

        countries = countries[offset:offset + limit]

        type_geo_output = request.query_params.get("type_geo_output", "simple")
        if type_geo_output not in ("feature", "simple"):
            return Response(data={"detail": "get param type_geo_output valid values ['feature', 'simple']"},
                            status=status.HTTP_400_BAD_REQUEST)

        if type_geo_output == "simple":
            result_data = {
                "count": count_data,
                "data": CountrySerializer(countries, many=True, remove_fields=remove_fields,
                                          type_geo_output=type_geo_output).data
            }
        else:
            result_data = geojson.FeatureCollection(CountrySerializer(countries, many=True, remove_fields=remove_fields,
                                                                      type_geo_output=type_geo_output).data)
            result_data["count"] = count_data

        return Response(data=result_data)

    def post(self, request: Request):
        country = CountrySerializer(data=request.data)
        country.is_valid(raise_exception=True)
        country.save()
        response = MyResponse(data=country.data)
        return response.to_response_api()

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
        response = MyResponse(data=country_data_update.data)
        return response.to_response_api()

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
