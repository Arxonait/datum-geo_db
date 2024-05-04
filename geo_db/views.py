import os
from functools import wraps

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from geo_db.additional_modules.decorators import get_standard_query_param
from geo_db.models import Country, City, Photo, GeoModel, Capital
from geo_db.mvc_view import output_many_geo_json_format, output_one_geo_json_format
from geo_db.additional_modules.pagination import pagination, Paginator
from geo_db.serializers import CountrySerializer, CitySerializer, BaseGeoSerializer, CapitalSerializer


class BaseAPI(APIView):
    model: GeoModel = None
    model_name: str = None
    serializer: BaseGeoSerializer = None

    def get_target_id_resource(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            obj_id = kwargs.get(self.model_name + "_id")
            if obj_id is None:
                return Response(data={"detail": f"{self.model_name} id is required"},
                                status=status.HTTP_400_BAD_REQUEST)
            try:
                obj = self.model.objects.get(pk=obj_id)
            except:
                return Response(data={"detail": f"{self.model_name} not found"}, status=status.HTTP_404_NOT_FOUND)

            return func(self, *args, obj=obj, **kwargs)

        return wrapper

    def post(self, request):
        obj = self.serializer(data=request.data)
        obj.is_valid(raise_exception=True)

        try:
            obj.save()
        except Exception as e:
            return Response({"detail": f"error: {e.args[0]}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data=obj.data, status=status.HTTP_201_CREATED)

    @get_target_id_resource
    def patch(self, request, obj, partial=True, **kwargs):
        obj_data_update = self.serializer(data=request.data, instance=obj, partial=partial)
        obj_data_update.is_valid(raise_exception=True)
        obj_data_update.save()
        return Response(data=obj_data_update.data, status=status.HTTP_200_OK)

    def put(self, request, **kwargs):
        return self.patch(request, partial=False, **kwargs)

    @get_target_id_resource
    def delete(self, request: Request, obj, **kwargs):
        obj_id = obj.pk
        obj.delete()
        return Response({"detail": f"delete {self.model_name} {obj_id}"})


class CountryAPI(BaseAPI):
    model: GeoModel = Country
    model_name: str = "country"
    serializer: BaseGeoSerializer = CountrySerializer

    @get_standard_query_param
    @pagination
    def get(self, request: Request, country_id=None, paginator: Paginator = None, bbox=None, type_geo_output=None,
            **kwargs):
        """
        query_params: \n
        limit, offset \n
        area: bool m^2 \n
        bbox x_min y_min x_max y_max \n
        type_geo_output ['simple', 'feature'] default simple
        total area: bool
        """

        add_fields = set()
        if request.query_params.get("area"):
            add_fields.add("area")

        if country_id is not None:
            countries = Country.model_filter(country_id=country_id)
            if len(countries) == 0:
                return Response(data={"detail": "country not found"}, status=status.HTTP_404_NOT_FOUND)
            result_data = output_one_geo_json_format(type_geo_output, CountrySerializer, countries, add_fields)
            return Response(data=result_data)

        # для нескольких объектов
        countries = Country.model_filter(bbox_coords=bbox)
        count_data = len(countries)

        countries = countries[paginator.offset: paginator.offset + paginator.limit]
        total_area = None
        if request.query_params.get("total_area", "false").lower() == "true":
            total_area = sum([obj.area for obj in countries])

        try:
            result_data = output_many_geo_json_format(type_geo_output, CountrySerializer, countries, paginator,
                                                      count_data, add_fields, total_area)
            return Response(data=result_data)
        except Exception as e:
            return Response(data={"detail": e.args[0]}, status=status.HTTP_400_BAD_REQUEST)


class CityAPI(BaseAPI):
    model: GeoModel = City
    model_name: str = "city"
    serializer: BaseGeoSerializer = CitySerializer

    @get_standard_query_param
    @pagination
    def get(self, request: Request, city_id=None, country_id=None, paginator: Paginator = None, bbox=None,
            type_geo_output=None, **kwargs):
        """
        query_params: \n
        limit, offset \n
        area: bool m^2 \n
        bbox x_min y_min x_max y_max \n
        type_geo_output ['simple', 'feature'] default simple
        total area: bool
        """

        add_fields = set()
        if request.query_params.get("area"):
            add_fields.add("area")

        if city_id is not None:
            cities = City.model_filter(city_id=city_id)
            if len(cities) == 0:
                return Response(data={"detail": "city not found"}, status=status.HTTP_404_NOT_FOUND)
            result_data = output_one_geo_json_format(type_geo_output, CitySerializer, cities, add_fields)
            return Response(data=result_data)

        # для нескольких объектов
        cities = City.model_filter(bbox_coords=bbox, country_id=country_id)
        count_data = len(cities)

        cities = cities[paginator.offset: paginator.offset + paginator.limit]
        total_area = None
        if request.query_params.get("total_area", "false").lower() == "true":
            total_area = sum([obj.area for obj in cities])

        try:
            result_data = output_many_geo_json_format(type_geo_output, CitySerializer, cities, paginator,
                                                      count_data, add_fields, total_area)
            return Response(data=result_data)
        except Exception as e:
            return Response(data={"detail": e.args[0]}, status=status.HTTP_400_BAD_REQUEST)


class ImagesCityAPI(APIView):

    def get_images(self, city_id, num_image, method="get"):
        if city_id is None:
            return Response({"detail": "city id is required"}, status=status.HTTP_400_BAD_REQUEST)
        if method == "delete" and num_image is None:
            return Response({"detail": "num image is required for delete"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            city = City.objects.get(pk=city_id)
        except:
            return Response({"detail": "city not found"}, status=status.HTTP_404_NOT_FOUND)

        photos = Photo.objects.filter(city_id=city.pk).order_by("time_created")
        total_images = len(photos)

        if num_image is None:
            return Response(data={"total_images": total_images}, status=status.HTTP_200_OK)

        if not (0 < num_image <= total_images):
            return Response({"detail": f"num_image in (1, ..., {total_images})"}, status=status.HTTP_400_BAD_REQUEST)

        return photos

    def get(self, request: Request, city_id, num_image: int = None):
        result = self.get_images(city_id, num_image)
        if isinstance(result, Response):
            return result

        return Response(data={
            "total_images": len(result),
            "number_image": num_image,
            "base64_image": result[num_image - 1].get_image_base64()
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

    def delete(self, request, city_id, num_image):
        result = self.get_images(city_id, num_image)
        if isinstance(result, Response):
            return result
        result[num_image - 1].delete() # todo
        return Response({"detail": f"delete image city {city_id} number image {num_image}"})


class CapitalAPI(BaseAPI):
    model: GeoModel = Capital
    model_name: str = "capital"
    serializer: BaseGeoSerializer = CapitalSerializer

    @get_standard_query_param
    @pagination
    def get(self, request: Request, capital_id=None, country_id=None, paginator: Paginator = None, bbox=None,
            type_geo_output=None, **kwargs):
        """
        query_params: \n
        limit, offset \n
        area: bool m^2 \n
        bbox x_min y_min x_max y_max \n
        type_geo_output ['simple', 'feature'] default simple
        total area: bool
        """

        add_fields = set()
        if request.query_params.get("area"):
            add_fields.add("area")

        if capital_id is not None or country_id is not None:
            capitals = Capital.model_filter(capital_id=capital_id, country_id=country_id)
            if len(capitals) == 0:
                return Response(data={"detail": "capital not found"}, status=status.HTTP_404_NOT_FOUND)
            result_data = output_one_geo_json_format(type_geo_output, CapitalSerializer, capitals, add_fields)
            return Response(data=result_data)

        # для нескольких объектов
        capitals = Capital.model_filter(bbox_coords=bbox)
        count_data = len(capitals)

        capitals = capitals[paginator.offset: paginator.offset + paginator.limit]
        total_area = None
        if request.query_params.get("total_area", "false").lower() == "true":
            total_area = sum([obj.area for obj in capitals])

        try:
            result_data = output_many_geo_json_format(type_geo_output, CapitalSerializer, capitals, paginator,
                                                      count_data, add_fields, total_area)
            return Response(data=result_data)
        except Exception as e:
            return Response(data={"detail": e.args[0]}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request, country_id=None):
        return super().post(request)

    def convert_country_to_capital(func):
        def wrapper(self, *args, capital_id=None, country_id=None, **kwargs):
            if country_id:
                capitals = Capital.model_filter(country_id=country_id)
                if len(capitals) != 1:
                    return Response(data={"detail": f"{self.model_name} not found"}, status=status.HTTP_404_NOT_FOUND)
                capital_id = capitals[0].pk
            kwargs["capital_id"] = capital_id
            return func(self, *args, **kwargs)

        return wrapper

    @convert_country_to_capital
    def put(self, request, capital_id):
        return self.patch(request, capital_id=capital_id, partial=False)

    @convert_country_to_capital
    def patch(self, request, capital_id, partial=True):
        return super().patch(request, capital_id, partial=partial)

    @convert_country_to_capital
    def delete(self, request, capital_id):
        return super().delete(request, capital_id)
