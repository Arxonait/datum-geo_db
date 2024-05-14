from enum import Enum

import geojson

from geo_db.additional_modules.pagination import Paginator


class TypeGeoOutput(Enum):
    feature = "feature"
    simple = "simple"

    @classmethod
    def get_default(cls):
        return cls.feature