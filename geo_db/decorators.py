from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response

from geo_db.mvc_view import TypeGeoOutput
from geo_db.validation import parse_valid_bbox


def get_standard_query_param(func):
    def wrapper(cls, request: Request, *args, **kwargs):
        try:
            type_geo_output = TypeGeoOutput(request.query_params.get("type_geo_output", TypeGeoOutput.get_default().value))
        except Exception as e:
            return Response(data={"detail": e.args[0]}, status=status.HTTP_400_BAD_REQUEST)

        bbox_coords = request.query_params.get("bbox")
        if bbox_coords:
            try:
                bbox_coords = parse_valid_bbox(request.query_params.get("bbox"))
            except Exception as e:
                return Response(data={"detail": e.args[0]}, status=status.HTTP_400_BAD_REQUEST)

        kwargs["get_params"] = {
            "type_geo_output": type_geo_output,
            "bbox": bbox_coords
        }
        return func(cls, request, *args, **kwargs)

    return wrapper
