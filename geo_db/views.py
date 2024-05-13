import os
from functools import wraps

import django_filters
import geojson
from django.http import Http404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from geo_db.additional_modules.decorators import get_standard_query_param
from geo_db.filters import CountryFilter, CityFilter
from geo_db.models import Country, City, Photo, GeoModel, Capital
from geo_db.mvc_view import output_many_geo_json_format, output_one_geo_json_format
from geo_db.additional_modules.pagination import pagination, Paginator, PaginatorLimitOffset, get_paginator
from geo_db.serializers import CountrySerializer, CitySerializer, BaseGeoSerializer, CapitalSerializer, \
    NewCountySerializer, FeatureCollectionSerializer, NewCitySerializer


class BaseAPI(APIView):
    model: GeoModel = None
    model_name: str = None
    serializer: BaseGeoSerializer = None

    def get_target_id_resource(func):
        """Находит и возвращает объект \n
        Требования к сслыкам --- имя ресурса + _id"""

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


class BaseViewSet(viewsets.ModelViewSet):
    def retrieve(self, request, *args, **kwargs):
        # instance = self.get_object()
        try:
            instance = self.get_queryset().get(pk=kwargs["pk"])
        except Exception:
            raise Http404(f"{self.name_model} matching query does not exist")
        feature = self.serializer_class(instance, context=self.get_serializer_context()).data
        return Response(feature)

    @pagination
    def list(self, request, *args, paginator: Paginator, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        feature_collection = FeatureCollectionSerializer.get_feature_collection(queryset, self.serializer_class,
                                                                                self.get_serializer_context(),
                                                                                paginator,
                                                                                request.query_params)
        return Response(feature_collection)


class CountryViewSet(BaseViewSet):
    # todo  type_geo_output ['simple', 'feature'] default feature
    queryset = Country.objects.all()
    serializer_class: CountrySerializer = NewCountySerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = CountryFilter
    name_model = "Country"

    # Отдаёт список городов страны
    @action(detail=True, methods=['GET'])
    def cities(self, request: Request, pk: int):
        paginator = get_paginator(request)
        queryset = City.objects.all().filter(country_id=pk)
        queryset = CityFilter(data=request.query_params, queryset=queryset).qs
        feature_collection = FeatureCollectionSerializer.get_feature_collection(queryset, NewCitySerializer,
                                                                                self.get_serializer_context(),
                                                                                paginator,
                                                                                request.query_params)
        return Response(feature_collection)


class CityViewSet(BaseViewSet):
    queryset = City.objects.all()
    serializer_class: NewCitySerializer = NewCitySerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = CityFilter
    name_model = "City"


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
        result[num_image - 1].delete()
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
        area: bool m^2 \n
        bbox x_min y_min x_max y_max \n
        type_geo_output ['simple', 'feature'] default feature \n
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
        """При создании столиц данные берутся только с тела запроса"""
        return super().post(request)

    def convert_country_to_capital(func):
        """Конвертирует id страны в id столицы"""

        def wrapper(self, *args, capital_id=None, country_id=None, **kwargs):
            if country_id:
                capitals = Capital.model_filter(country_id=country_id)
                if len(capitals) != 1:
                    return Response(data={"detail": f"{self.model_name} not found"}, status=status.HTTP_404_NOT_FOUND)
                capital_id = capitals[0].pk
            return func(self, *args, **kwargs, capital_id=capital_id)

        return wrapper

    @convert_country_to_capital
    def put(self, request, **kwargs):
        return self.patch(request, partial=False, **kwargs)

    @convert_country_to_capital
    def patch(self, request, partial=True, **kwargs):
        return super().patch(request, partial=partial, **kwargs)

    @convert_country_to_capital
    def delete(self, request, **kwargs):
        return super().delete(request, **kwargs)
