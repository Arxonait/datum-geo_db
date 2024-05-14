import base64
import os
import uuid

from django.contrib.gis.db import models
from django.contrib.gis.geos import Polygon
from django.core.files.base import ContentFile
from osgeo import ogr
from pyproj import Transformer

crs_from = "epsg:4326"
crs_to = "epsg:32633"
transformer = Transformer.from_crs(crs_from, crs_to, always_xy=True)


class GeoModel(models.Model):
    objects = models.Manager()

    class Meta:
        abstract = True

    name = models.CharField(max_length=255)
    coordinates = models.PolygonField()

    def __str__(self):
        return f"Name: {self.name}"

    @property
    def area(self):
        """Площадь в квадратных метрах"""
        coords_degrees = self.coordinates.coords[0]
        coords_meters = [transformer.transform(lon, lat) for lon, lat in coords_degrees]
        ring = ogr.Geometry(ogr.wkbLinearRing)
        for x, y in coords_meters:
            ring.AddPoint(x, y)

        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)

        area = poly.GetArea()
        return round(area, 4)


class Country(GeoModel):
    class Meta:
        verbose_name = "Страна"
        verbose_name_plural = "Страны"


class City(GeoModel):
    description = models.TextField()
    country = models.ForeignKey("Country", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Город"
        verbose_name_plural = "Города"


class Capital(GeoModel):
    country = models.OneToOneField("Country", on_delete=models.CASCADE)

    class Meta:
        verbose_name = "Столица"
        verbose_name_plural = "Столицы"


class Photo(models.Model):
    image = models.ImageField(upload_to=os.getenv("IMAGES_PATH"))
    time_created = models.DateTimeField(auto_now_add=True)
    city = models.ForeignKey("City", on_delete=models.CASCADE, related_name='images')

    def __init__(self, *args, base64_image: str = None, **kwargs):
        super().__init__(*args, **kwargs)
        if base64_image is not None:
            self.image = self.__decode_base64_image_to_file(base64_image)

    def __decode_base64_image_to_file(self, base64_image: str):
        image_data = base64.b64decode(base64_image)
        return ContentFile(image_data, name=self.__get_new_image_name())

    def get_image_base64(self):
        with self.image.open(mode='rb') as img_file:
            img_data = img_file.read()

        return base64.b64encode(img_data).decode('utf-8')

    def __get_new_image_name(self):
        return f'{self.city.id}_{str(uuid.uuid4())[:7]}.jpg'

    def delete(self, *args, **kwargs):
        # Удаление связанного файла перед удалением объекта
        self.image.delete()
        super().delete(*args, **kwargs)
