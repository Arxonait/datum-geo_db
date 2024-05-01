import geojson


def output_geo_json_format(type_geo_output: str, ClassSerilizer, data, count_data,
                           add_fields: set = None):
    if type_geo_output not in ("feature", "simple"):
        raise Exception("get param type_geo_output valid values ['feature', 'simple']")

    if type_geo_output == "simple":
        result_data = {
            "count": count_data,
            "data": ClassSerilizer(data, many=True, add_fields=add_fields, type_geo_output=type_geo_output).data
        }
    else:
        result_data = geojson.FeatureCollection(ClassSerilizer(data, many=True, add_fields=add_fields,
                                                               type_geo_output=type_geo_output).data)
        result_data["count"] = count_data
    return result_data
