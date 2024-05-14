import os

import django_filters
from django.http import Http404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from geo_db.additional_modules.pagination import pagination, Paginator, get_paginator
from geo_db.filters import CountryFilter, CityFilter, CapitalFilter
from geo_db.models import Country, City, Photo, Capital
from geo_db.serializers import CountySerializer, DataCollectionSerializer, CitySerializer, CapitalSerializer


class BaseViewSet(viewsets.ModelViewSet):

    def get_serializer_context(self):
        context = {}
        if "area" in self.request.query_params:
            context["area"] = True
        return context

    def get_target_obj(self, pk):
        queryset = self.get_queryset().filter(pk=pk)
        if len(queryset) != 1:
            raise Http404(f"{self.name_model} not found")
        return queryset

    def retrieve(self, request, *args, pk, **kwargs):
        queryset = self.get_target_obj(pk)
        feature = self.serializer_class(queryset, context=self.get_serializer_context()).data
        return Response(feature)

    @pagination
    def list(self, request, *args, paginator: Paginator, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        feature_collection = DataCollectionSerializer.get_feature_collection(queryset, self.serializer_class,
                                                                             self.get_serializer_context(),
                                                                             paginator,
                                                                             request.query_params)
        return Response(feature_collection)


class CountryViewSet(BaseViewSet):
    queryset = Country.objects.all()
    serializer_class: CountySerializer = CountySerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = CountryFilter
    name_model = "Country"

    # Отдаёт список городов страны
    @action(detail=True, methods=['GET'])
    def cities(self, request: Request, pk: int):
        paginator = get_paginator(request)
        self.get_target_obj(pk)
        queryset = City.objects.all().filter(country_id=pk)
        queryset = CityFilter(data=request.query_params, queryset=queryset).qs
        feature_collection = DataCollectionSerializer.get_feature_collection(queryset, CitySerializer,
                                                                             self.get_serializer_context(),
                                                                             paginator,
                                                                             request.query_params)
        return Response(feature_collection)

    @action(detail=True, methods=['GET'])
    def capital(self, request: Request, pk: int):
        self.get_target_obj(pk)
        queryset = Capital.objects.filter(country_id=pk)
        if len(queryset) != 1:
            raise Http404(f"capital not found")
        data = queryset[0]
        feature = self.serializer_class(data, context=self.get_serializer_context()).data
        return Response(feature)

    @capital.mapping.post
    def post_capital(self, request: Request, pk: int):
        self.get_target_obj(pk)

        obj = CapitalSerializer(data=request.data)
        obj.is_valid(raise_exception=True)

        try:
            obj.save()
        except Exception as e:
            return Response({"detail": f"error: {e.args[0]}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data=obj.data, status=status.HTTP_201_CREATED)

    @capital.mapping.delete
    def delete_capital(self, request: Request, pk: int):
        self.get_target_obj(pk)
        queryset = Capital.objects.filter(country_id=pk)
        if len(queryset) != 1:
            raise Http404(f"capital not found")
        data = queryset[0]
        obj_id = data.pk
        data.delete()
        return Response({"detail": f"delete capital {obj_id}"})

    @capital.mapping.put
    def put_capital(self, request: Request, pk: int):
        self.get_target_obj(pk)
        queryset = Capital.objects.filter(country_id=pk)
        if len(queryset) != 1:
            raise Http404(f"capital not found")

        obj = CapitalSerializer(data=request.data)
        obj.is_valid(raise_exception=True)

        try:
            obj.save()
        except Exception as e:
            return Response({"detail": f"error: {e.args[0]}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data=obj.data, status=status.HTTP_200_OK)

    @capital.mapping.patch
    def patch_capital(self, request: Request, pk: int):
        self.get_target_obj(pk)
        queryset = Capital.objects.filter(country_id=pk)
        if len(queryset) != 1:
            raise Http404(f"capital not found")

        capital = queryset[0]

        obj = CapitalSerializer(data=request.data, instance=capital, partial=True)
        obj.is_valid(raise_exception=True)

        try:
            obj.save()
        except Exception as e:
            return Response({"detail": f"error: {e.args[0]}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(data=obj.data, status=status.HTTP_200_OK)


class CityViewSet(BaseViewSet):
    queryset = City.objects.all()
    serializer_class: CitySerializer = CitySerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = CityFilter
    name_model = "City"

    def get_images(self, city_id, num_image):
        photos = Photo.objects.filter(city_id=city_id).order_by("time_created")
        total_images = len(photos)

        if num_image is None:
            return Response(data={"total_images": total_images}, status=status.HTTP_200_OK)

        if not (0 < num_image <= total_images):
            return Response({"detail": f"num_image in (1, ..., {total_images})"}, status=status.HTTP_400_BAD_REQUEST)

        return photos

    @action(detail=True, methods=['GET'], url_path='images(?:/(?P<num_image>\d+))?')
    def images(self, request: Request, pk: int, num_image: int = None):
        self.get_target_obj(pk)
        if num_image is not None:
            num_image = int(num_image)

        result = self.get_images(pk, num_image)
        if isinstance(result, Response):
            return result

        return Response(data={
            "total_images": len(result),
            "number_image": num_image,
            "base64_image": result[num_image - 1].get_image_base64()
        },
            status=status.HTTP_200_OK)

    @images.mapping.delete
    def image_delete(self, request, pk: int, num_image: int = None):
        if num_image is None:
            return Response({"detail": "num image is required for delete"}, status=status.HTTP_400_BAD_REQUEST)

        num_image = int(num_image)
        result = self.get_images(pk, num_image)

        if isinstance(result, Response):
            return result
        result[num_image - 1].delete()
        return Response({"detail": f"delete image city {pk} number image {num_image}"})

    @images.mapping.post
    def image_post(self, request: Request, pk, *args, **kwargs):
        os.makedirs(os.path.dirname(r"media/"), exist_ok=True)
        city_qs = self.get_target_obj(pk)

        base64_image = request.data.get("base64_image")
        if base64_image is None:
            return Response({"detail": "base64_image is required"}, status=status.HTTP_400_BAD_REQUEST)

        photo = Photo(city=city_qs[0], base64_image=base64_image)
        photo.save()
        return Response(data={"status": "created"}, status=status.HTTP_201_CREATED)


class CapitalViewSet(BaseViewSet):
    queryset = Capital.objects.all()
    serializer_class: CapitalSerializer = CapitalSerializer
    filter_backends = [django_filters.rest_framework.DjangoFilterBackend]
    filterset_class = CapitalFilter
    name_model = "Capital"




