def parse_valid_bbox(bbox: str):
    bbox_coords = bbox.split()
    bbox_coords = [float(coord) for coord in bbox_coords]

    if len(bbox_coords) != 4:
        raise Exception("bbox required format x_min y_min x_max y_max")

    return bbox_coords
