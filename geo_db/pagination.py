

def pagination(func):
    def wrapper(cls, request, *args, **kwargs):
        limit = int(request.query_params.get("limit", 10))
        offset = int(request.query_params.get("offset", 0))
        if limit <= 0:
            limit = 10
        if offset < 0:
            offset = 0
        return func(cls, request, *args, **kwargs, limit=limit, offset=offset)

    return wrapper
