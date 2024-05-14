import base64
import uuid

from django.contrib.gis.db import models
from django.core.files.base import ContentFile
from osgeo import ogr
from pyproj import Transformer



class GeoModel(models.Model):
    objects = models.Manager()

    class Meta:
        abstract = True

    name = models.CharField(max_length=255)
    coordinates = models.PolygonField(srid=4326, geography=True)

    def __str__(self):
        return f"Name: {self.name}"


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
    image = models.ImageField(upload_to="media/")
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
        return f'{self.city.id}_{str(uuid.uuid4())[:7]}.png'

    def delete(self, *args, **kwargs):
        # Удаление связанного файла перед удалением объекта
        self.image.delete()
        super().delete(*args, **kwargs)
