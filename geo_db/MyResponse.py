from rest_framework import status
from rest_framework.response import Response


class MyResponse:
    def __init__(self, data = None, count_data=None, detail: str = None, status_code=status.HTTP_200_OK):
        if isinstance(data, list) and count_data is None:
            raise Exception("count_data is required")

        if isinstance(data, list) and count_data > 1:
            self.data = {
                "count_items": count_data,
                "items": data
            }
        elif data is not None:
            self.data = data if isinstance(data, dict) else data[0]
        else:
            self.data = {}
        self.detail = detail
        self.status_code = status_code

    def to_response_api(self):
        return Response(data={
            "data": self.data,
            "detail": self.detail
        }, status=self.status_code)
