import base64

from django.contrib.gis.geos import Polygon
from django.test import TestCase

TEST_POLYGON = ((19.298488064150035, 43.510902041818866),
                (19.528309386031935, 43.24686866222709),
                (20.179459092915266, 42.82572783537185),
                (19.298488064150035, 43.510902041818866))


class BaseEndpoints(TestCase):
    fixtures = ["test_country", ]

    def test_format_feature_target_obj(self):
        url = "/api/countries/1/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data["type"], str)
        self.assertEqual(data["type"], "Feature")
        self.assertIsInstance(data["properties"], dict)
        self.assertIsInstance(data["geometry"], dict)
        self.assertIsInstance(data["geometry"]["type"], str)
        self.assertIsInstance(data["geometry"]["coordinates"], list)

    def test_format_feature_collection(self):
        url = "/api/countries/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data["type"], str)
        self.assertEqual(data["type"], "FeatureCollection")
        self.assertIsInstance(data["features"], list)

    def test_create_point(self):
        url = "/api/countries/"
        data = {
            "name": "test",
            "coordinates": "Point(20.0 20.0)"
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 400)

    def sup_create_wrong_format_wkt_polygon(self, polygon_wkt: str, status_code):
        url = "/api/countries/"
        data = {
            "name": "test",
            "coordinates": polygon_wkt
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status_code)

    def test_format_wkt_polygon(self):
        self.sup_create_wrong_format_wkt_polygon("Polygon((30 10, 40 40, 20 40, 10 20, 30 10))", 201)
        self.sup_create_wrong_format_wkt_polygon("POLYGON((30 10, 40 40, 20 40, 10 20, 30 10))", 201)
        self.sup_create_wrong_format_wkt_polygon("Polygon((30 10, 40 40, 20 40, 10 20))", 400)


class EndpointCountry(TestCase):
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

    def sup_countries_bbox(self, countries: tuple[str], bbox: str):
        url = "/api/countries/"
        response = self.client.get(url + f"?bbox={bbox}")
        self.assertEqual(response.status_code, 200)
        for country in countries:
            self.assertContains(response, country)

    def test_countries_bbox(self):
        self.sup_countries_bbox(("serbia",), "14.29368212620912 34.6381741548327 42.19753730351246 48.57334147892965")
        self.sup_countries_bbox(("serbia", "turkey"), "14.533444941126703 32.43752552067821 46.39631982796453 48.66047888075295")
        self.sup_countries_bbox(("serbia",), "16.65426881144313 41.232741282364515 25.591189909754917 48.07800474300802")

    def test_get_country_area(self):
        url = "/api/countries/1/?area"
        response = self.client.get(url)
        self.assertContains(response, "area")

    def test_get_countries_area(self):
        url = "/api/countries/?area"
        response = self.client.get(url)
        self.assertContains(response, "area")

    def test_get_countries_area_total_area(self):
        url = "/api/countries/?area&total_area"
        response = self.client.get(url)
        self.assertContains(response, "area")
        self.assertContains(response, "total_area")

    def test_get_country_total_area_without_area(self):
        url = "/api/countries/?total_area"
        response = self.client.get(url)
        self.assertContains(response, "total_area")


class EndpointCity(TestCase):
    fixtures = ["test_country", "test_city"]

    def sup_city_bbox(self, city: tuple[str], bbox: str):
        url = "/api/cities/"
        response = self.client.get(url + f"?bbox={bbox}")
        self.assertEqual(response.status_code, 200)
        for city in city:
            self.assertContains(response, city)

    def test_city_bbox(self):
        self.sup_city_bbox(("opornica", "resnik"), "20.828530482799607 44.04283412827576 20.954330958696545 44.12627250468475")
        self.sup_city_bbox(("resnik",), "20.890127310203695 44.103420443101044 20.951539625376938 44.13638003111589")


class EndpointImage(TestCase):
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
