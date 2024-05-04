from enum import Enum

import geojson

from geo_db.additional_modules.pagination import Paginator


class TypeGeoOutput(Enum):
    feature = "feature"
    simple = "simple"

    @classmethod
    def get_default(cls):
        return cls.feature


def output_many_geo_json_format(type_geo_output: TypeGeoOutput, ClassSerilizer, data, paginator: Paginator, count_data,
                                add_fields: set = None, total_area: float = None):

    previous_link, next_link = paginator.get_links_pagination(count_data)
    result_data = {
        "count": count_data,
        "previous_link": previous_link,
        "next_link": next_link
    }

    if total_area:
        result_data["total_area"] = total_area

    if type_geo_output == TypeGeoOutput.simple:
        result_data["data"] = ClassSerilizer(data, many=True, add_fields=add_fields, type_geo_output=type_geo_output).data
    else:
        result_data.update(geojson.FeatureCollection(ClassSerilizer(data, many=True, add_fields=add_fields,
                                                                    type_geo_output=type_geo_output).data))
    return result_data


def output_one_geo_json_format(type_geo_output: TypeGeoOutput, ClassSerilizer, data, add_fields: set = None):
    return ClassSerilizer(data, many=True, add_fields=add_fields, type_geo_output=type_geo_output).data[0]
