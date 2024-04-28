import os

from django.contrib.gis.db import models
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

    def get_area(self):
        """Площадь в квадратных метрах"""
        coords_degrees = self.coordinates.coords[0]
        coords_meters = [transformer.transform(lon, lat) for lon, lat in coords_degrees]
        ring = ogr.Geometry(ogr.wkbLinearRing)
        for x, y in coords_meters:
            ring.AddPoint(x, y)

        poly = ogr.Geometry(ogr.wkbPolygon)
        poly.AddGeometry(ring)

        area = poly.GetArea()
        return area


class Country(GeoModel):
    class Meta:
        verbose_name = "Страны"
        verbose_name_plural = "Страны"


class City(GeoModel):
    description = models.TextField()
    country = models.ForeignKey("Country", on_delete=models.CASCADE)


class Capital(GeoModel):
    country = models.ForeignKey("Country", on_delete=models.CASCADE)


class Photo(models.Model):
    image = models.ImageField(upload_to=os.getenv("IMAGES_PATH"))  # todo  определить папку
    city = models.ForeignKey("City", on_delete=models.CASCADE, related_name='images')
