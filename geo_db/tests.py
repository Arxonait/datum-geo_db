import base64

from django.contrib.gis.geos import Polygon
from django.test import TestCase

TEST_POLYGON = ((19.298488064150035, 43.510902041818866),
                (19.528309386031935, 43.24686866222709),
                (20.179459092915266, 42.82572783537185),
                (19.298488064150035, 43.510902041818866))
BBOX_ARRAY = [
    (("serbia",), "14.29368212620912 34.6381741548327 42.19753730351246 48.57334147892965"),
    (("serbia", "turkey"), "14.533444941126703 32.43752552067821 46.39631982796453 48.66047888075295"),
    (("serbia",), "16.65426881144313 41.232741282364515 25.591189909754917 48.07800474300802"),
    ((), "14.29368212620912 34.6381741548327 42.19753730351246 48.57334147892965"),
]


# Create your tests here.
class MyEndpointCountry(TestCase):
    fixtures = ["test_country", ]

    def test_create_countries(self):
        url = "/api/countries/"
        data = {
            "name": "test",
            "coordinates": Polygon(TEST_POLYGON).wkt
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_patch_countries(self):
        url = "/api/countries/1/"
        data = {
                "name": "test88"
                }
        response = self.client.patch(url, data=data, content_type="application/json")
        self.assertContains(response, "test88")

    def test_delete_country(self):
        url = "/api/countries/2/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

    def test_get_country_not_found(self):
        url = "/api/countries/50/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_countries_bbox(self):
        url = "/api/countries/"
        for countries, bbox in BBOX_ARRAY:
            response = self.client.get(url + f"?bbox={bbox}")
            self.assertEqual(response.status_code, 200)
            for country in countries:
                self.assertContains(response, country)


class MyEndpointImage(TestCase):
    fixtures = ["test_country", "test_city"]

    def test_endpoint_images(self):
        url = f"/api/cities/2/images/"

        with open(r"media/test/test_image.png", "rb") as image_file:
            binary_data = image_file.read()
        base64_data = base64.b64encode(binary_data)

        data = {
            "base64_image": base64_data.decode("utf-8")
        }
        response = self.client.post(url, data=data, content_type="application/json")
        self.assertContains(response, "created", status_code=201)

        response = self.client.get(url + "1/")
        self.assertContains(response, "base64_image", status_code=200)

        data = response.json()
        binary_data = base64.b64decode(data["base64_image"])

        # with open("test.png", 'wb') as file:
        #     file.write(binary_data)

        response = self.client.delete(url + "1/")
        self.assertContains(response, "delete image", status_code=200)
