from rest_framework.request import Request


def pagination(func):
    def wrapper(cls, request: Request, *args, **kwargs):
        limit = int(request.query_params.get("limit", 10))
        offset = int(request.query_params.get("offset", 0))
        if limit <= 0:
            limit = 10
        if offset < 0:
            offset = 0

        url = request.build_absolute_uri()
        url = url.split("?")[0] + "?"
        for query_param in request.query_params.items():
            if query_param[0] not in ("limit", "offset"):
                url += f"{query_param[0]}={query_param[1]}&"
        pagination_data = {
            "url": url,
            "limit": limit,
            "offset": offset
        }

        return func(cls, request, *args, **kwargs, pagination_data=pagination_data)

    return wrapper


def create_links_pagination_limit_offset(pagination_data, count_data):
    url = pagination_data["url"]
    limit = pagination_data["limit"]
    offset = pagination_data["offset"]
    next_link = None
    if offset + limit <= count_data:
        next_link = url + f"offset={offset + limit}&limit={limit}"

    previous_link = None
    if offset != 0:
        previous_link = url + f"offset={max(0, offset - limit)}&limit={limit}"
    return previous_link, next_link
