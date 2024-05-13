import base64

import pandas
from django.test import TestCase

from geo_db.models import Country, City

URL = "http://127.0.0.1:8000/api/"
COORDINATE_TEST = ("POLYGON((29.62999999999999 46.84000000001423, 29.62999999999999 46.84160000001423, "
                   "29.63849999999999 46.84160000001423, 29.63849999999999 46.84000000001423, 29.62999999999999 "
                   "46.84000000001423))")


# Create your tests here.
class MyEndpointCountry(TestCase):
    def setUp(self):
        self.countries = []
        table_countries = pandas.read_csv(r"countries.csv", delimiter=";")
        for index, row in table_countries.iterrows():
            country = Country(name=row["name"], coordinates=row["coordinates"])
            country.save()
            self.countries.append(country)

        table_cities = pandas.read_csv(r"cities.csv", delimiter=";")
        for index, row in table_cities.iterrows():
            City(name=row["name"], coordinates=row["coordinates"], description="foo",
                 country=self.countries[row["country_id"] - 1]).save()

        self.bbox_data = []
        table_bbox = pandas.read_csv(r"bbox.csv", delimiter=";")
        for index, row in table_bbox[table_bbox["type"] == "country"].iterrows():
            self.bbox_data.append((row["bbox"], len(row["obj"].split(",") if isinstance(row["obj"], str) else "")))

    def test_endpoint_countries_create_patch_delete_get(self):
        url = URL + "countries/"

        data = {
            "name": "test88",
            "coordinates": COORDINATE_TEST
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)
        print("test_endpoint_countries_create_patch_delete_get --- pass --- created")

        res_data = response.json()
        url += f"{res_data['id']}/"

        response = self.client.patch(url, data={"name": "test99"}, content_type="application/json")
        self.assertContains(response, "test99")
        print("test_endpoint_countries_create_patch_delete_get --- pass --- change")

        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        print("test_endpoint_countries_create_patch_delete_get --- pass --- delete")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        print("test_endpoint_countries_create_patch_delete_get --- pass --- get(not found)")

    def test_countries_bbox(self):
        url = URL + "countries/"
        for bbox_data in self.bbox_data:
            response = self.client.get(url + f"?bbox={bbox_data[0]}")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["count"], bbox_data[1])
            print("test_countries_bbox --- pass")


class MyEndpointImage(TestCase):
    def setUp(self):
        country = Country(name="testtt",
                          coordinates=COORDINATE_TEST)
        country.save()

        city = City(name="testtt", coordinates=COORDINATE_TEST,  description="foo", country=country)
        city.save()
        self.city = city

    def test_endpoint_images(self):
        url = URL + f"cities/{self.city.pk}/images"
        
        with open("D:/testimg.png", "rb") as image_file:
            binary_data = image_file.read()
        base64_data = base64.b64encode(binary_data)

        data = {
            "base64_image": str(base64_data)
        }
        response = self.client.post(url, data=data, content_type="application/json")
        self.assertContains(response, "created", status_code=201)
        print("test_endpoint_images --- pass --- image upload")

        response = self.client.get(url + "/1")
        self.assertContains(response, "base64_image", status_code=200)

        data = response.json()
        binary_data = base64.b64decode(data["base64_image"])

        with open("test.png", 'wb') as file:
            file.write(binary_data)

        print("test_endpoint_images --- pass --- image download")

        response = self.client.delete(url + "/1")
        self.assertContains(response, "delete image", status_code=200)

        print("test_endpoint_images --- pass --- image deleted")