import os

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from geo_db.decorators import get_standard_query_param
from geo_db.models import Country, City, Photo, GeoModel
from geo_db.mvc_model import model_country, model_city
from geo_db.mvc_view import output_many_geo_json_format, output_one_geo_json_format
from geo_db.pagination import pagination
from geo_db.serializers import CountrySerializer, CitySerializer, BaseGeoSerializer


class BaseAPI(APIView):
    model: GeoModel = None
    model_name: str = None
    serializer: BaseGeoSerializer = None

    def post(self, request):
        obj = self.serializer(data=request.data)
        obj.is_valid(raise_exception=True)

        try:
            obj.save()
        except Exception as e:
            return Response({"detail": f"error: {e.args}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data=obj.data, status=status.HTTP_201_CREATED)

    def patch(self, request, obj_id=None, partial=True):
        if obj_id is None:
            return Response(data={"detail": f"{self.model_name} id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            obj = self.model.objects.get(pk=obj_id)
        except:
            return Response(data={"detail": f"{self.model_name} not found"}, status=status.HTTP_404_NOT_FOUND)

        obj_data_update = self.serializer(data=request.data, instance=obj, partial=partial)
        obj_data_update.is_valid(raise_exception=True)
        obj_data_update.save()
        return Response(data=obj_data_update.data, status=status.HTTP_200_OK)

    def put(self, request, obj_id=None):
        return self.patch(request, obj_id, partial=False)

    def delete(self, request: Request, obj_id):
        if obj_id is None:
            return Response(data={"detail": f"{self.model_name} id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            country = self.model.objects.get(pk=obj_id)
        except:
            return Response(data={"detail": f"{self.model_name} not found"}, status=status.HTTP_404_NOT_FOUND)

        country.delete()

        return Response({"detail": f"delete {self.model_name} {obj_id}"})


class CountryAPI(BaseAPI):
    model: GeoModel = Country
    model_name: str = "country"
    serializer: BaseGeoSerializer = CountrySerializer

    @get_standard_query_param
    @pagination
    def get(self, request: Request, obj_id=None, pagination_data=None, **kwargs):
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

        if obj_id is not None:
            countries = model_country(country_id=obj_id)
            if len(countries) == 0:
                return Response(data={"detail": "country not found"}, status=status.HTTP_404_NOT_FOUND)
            result_data = output_one_geo_json_format(type_geo_output, CountrySerializer, countries, add_fields)
            return Response(data=result_data)


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


class CityAPI(BaseAPI):
    model: GeoModel = City
    model_name: str = "city"
    serializer: BaseGeoSerializer = CitySerializer

    @get_standard_query_param
    @pagination
    def get(self, request: Request, obj_id=None, country_id=None, pagination_data=None, **kwargs):
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

        if obj_id is not None:
            cities = model_city(city_id=obj_id)
            if len(cities) == 0:
                return Response(data={"detail": "city not found"}, status=status.HTTP_404_NOT_FOUND)
            result_data = output_one_geo_json_format(type_geo_output, CitySerializer, cities, add_fields)
            return Response(data=result_data)


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


class ImagesCityAPI(APIView):

    def get(self, request: Request, city_id, num_image: int = None):
        if city_id is None:
            return Response({"detail": "city id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            city = City.objects.get(pk=city_id)
        except:
            return Response({"detail": "city not found"}, status=status.HTTP_404_NOT_FOUND)

        photos = Photo.objects.filter(city_id=city.pk).order_by("time_created")
        total_images = len(photos)

        if num_image is None:
            return Response(data={
                "total_images": total_images,
            }, status=status.HTTP_200_OK)

        if not (0 < num_image <= total_images):
            return Response({"detail": f"num_image in (1, ..., {total_images})"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data={
            "total_images": total_images,
            "number_image": num_image,
            "base64_image": photos[num_image - 1].get_image_base64()
        },
            status=status.HTTP_200_OK)

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
