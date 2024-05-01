import geojson

from geo_db.pagination import create_links_pagination_limit_offset


def output_many_geo_json_format(type_geo_output: str, ClassSerilizer, data, pagination_data: dict, count_data,
                                add_fields: set = None):
    if type_geo_output not in ("feature", "simple"):
        raise Exception("get param type_geo_output valid values ['feature', 'simple']")

    previous_link, next_link = create_links_pagination_limit_offset(pagination_data, count_data)
    result_data = {
        "count": count_data,
        "previous_link": previous_link,
        "next_link": next_link
    }

    if type_geo_output == "simple":
        result_data["data"] = ClassSerilizer(data, many=True, add_fields=add_fields,
                                             type_geo_output=type_geo_output).data
    else:
        result_data.update(geojson.FeatureCollection(ClassSerilizer(data, many=True, add_fields=add_fields,
                                                                    type_geo_output=type_geo_output).data))
    return result_data


def output_one_geo_json_format(type_geo_output: str, ClassSerilizer, data, add_fields: set = None):
    if type_geo_output not in ("feature", "simple"):
        raise Exception("get param type_geo_output valid values ['feature', 'simple']")

    return ClassSerilizer(data, many=True, add_fields=add_fields, type_geo_output=type_geo_output).data[0]
