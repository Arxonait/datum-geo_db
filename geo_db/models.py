from django.contrib.gis.db import models


class GeoModel(models.Model):
    class Meta:
        abstract = True

    name = models.CharField(max_length=255)
    coordinates = models.PointField()

    def __str__(self):
        return f"Name: {self.name}"


class Country(GeoModel):
    pass


class City(GeoModel):
    description = models.TextField()
    #images = models.TextField()
    country = models.ForeignKey("Country", on_delete=models.CASCADE)


class Capital(GeoModel):
    country = models.ForeignKey("Country", on_delete=models.CASCADE)
