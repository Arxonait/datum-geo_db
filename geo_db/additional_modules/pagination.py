from abc import ABC, abstractmethod

from rest_framework.request import Request


def pagination(func):
    def wrapper(cls, request: Request, *args, **kwargs):
        paginator = get_paginator(request)
        return func(cls, request, *args, **kwargs, paginator=paginator)
    return wrapper


class Paginator(ABC):

    def __init__(self, request: Request):
        self._request = request
        data = self._parse_value_pagination()
        self.limit, self.offset = self._convert_to_limit_offset(data)

    @classmethod
    @abstractmethod
    def get_name_pagination_query_params(cls) -> tuple:
        ...

    def _get_url_without_pagination(self):
        url = self._request.build_absolute_uri()
        url = url.split("?")[0] + "?"
        for query_param in self._request.query_params.items():
            if query_param[0] not in self.get_name_pagination_query_params():
                url += f"{query_param[0]}={query_param[1]}&"
        return url

    def _set_default_limit(self):
        return 10

    def _set_default_offset(self):
        return 0

    @abstractmethod
    def _parse_value_pagination(self):
        ...

    @abstractmethod
    def _convert_to_limit_offset(self, data) -> (int, int):
        ...

    @abstractmethod
    def get_links_pagination(self, count_data: int) -> (str, str):
        ...

    def get_start(self):
        return self.offset

    def get_end(self):
        return self.offset + self.limit

    def get_pagination_data(self, count_data: int):
        previous_link, next_link = self.get_links_pagination(count_data)
        return {
                "count": count_data,
                "previous_link": previous_link,
                "next_link": next_link
                }


class PaginatorLimitOffset(Paginator):
    @classmethod
    def get_name_pagination_query_params(cls) -> tuple:
        return "limit", "offset"

    def _parse_value_pagination(self):
        limit = int(self._request.query_params.get("limit", self._set_default_limit()))
        offset = int(self._request.query_params.get("offset", self._set_default_offset()))
        if limit <= 0 or offset < 0:
            limit = self._set_default_limit()
            offset = self._set_default_offset()
        return limit, offset

    def _convert_to_limit_offset(self, data) -> (int, int):
        return data

    def get_links_pagination(self, count_data: int) -> (str, str):
        next_link = None
        if self.offset + self.limit <= count_data:
            next_link = self._get_url_without_pagination() + f"offset={self.offset + self.limit}&limit={self.limit}"

        previous_link = None
        if self.offset != 0:
            previous_link = self._get_url_without_pagination() + f"offset={max(0, self.offset - self.limit)}&limit={self.limit}"
        return previous_link, next_link


class PaginatorPage(Paginator):
    @classmethod
    def get_name_pagination_query_params(cls) -> tuple:
        return ("page",)

    def _parse_value_pagination(self):
        page = int(self._request.query_params.get("page", 1))
        if page <= 0:
            page = 1
        return page

    def _convert_to_limit_offset(self, data) -> (int, int):
        page = data
        page -= 1
        limit = self._set_default_limit()
        offset = self._set_default_limit() * page
        return limit, offset

    def get_links_pagination(self, count_data: int) -> (str, str):
        next_link = None
        if self.offset + self.limit < count_data:
            next_link = self._get_url_without_pagination() + f"page={int(self.offset / self.limit + 2)}"

        previous_link = None
        if self.offset != 0:
            previous_link = self._get_url_without_pagination() + f"page={int(self.offset / self.limit)}"
        return previous_link, next_link


def get_paginator(request):
    query_params = request.query_params.keys()

    if len(set(query_params) & set(PaginatorLimitOffset.get_name_pagination_query_params())) != 0:
        paginator = PaginatorLimitOffset(request)
    elif len(set(query_params) & set(PaginatorPage.get_name_pagination_query_params())) != 0:
        paginator = PaginatorPage(request)
    else:
        paginator = PaginatorLimitOffset(request)

    return paginator
