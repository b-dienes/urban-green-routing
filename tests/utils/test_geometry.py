import pytest
from utils.inputs import UserInput, RoutingPreference
from utils.geometry import BoundingBoxMercator, bounding_box_mercator, tile_calculator

"""
Tests for utils.geometry

Function tested: bounding_box_mercator(user_input)
- Converts WGS84 lat/lon to EPSG:3857 Mercator
- Returns BoundingBoxMercator

Test categories:
- Normal cases: typical valid coordinates
- Edge cases: extreme lat/lon (poles, dateline)
"""

def test_bounding_box_mercator_normal_coordinates():
    """
    Typical valid coordinates (SW < NE)
    Verify:
    - Returned object is BoundingBoxMercator
    - xmin < xmax, ymin < ymax
    - Rough numeric check of expected transformed coordinates
    """
    user_input = UserInput(
        aoi_name = "test_aoi",
        sw_lat = 0,
        sw_lon = 0,
        ne_lat = 1,
        ne_lon = 1,
        resolution = 1,
        routing_source = 1,
        routing_target = 2,
        routing_weight = RoutingPreference.SHORTEST)

    bbox_mercator = bounding_box_mercator(user_input)

    assert isinstance(bbox_mercator, BoundingBoxMercator)

    assert bbox_mercator.xmin < bbox_mercator.xmax
    assert bbox_mercator.ymin < bbox_mercator.ymax

    assert bbox_mercator.xmin == 0
    assert bbox_mercator.ymin == 0
    assert 111000 < bbox_mercator.xmax < 112000
    assert 111000 < bbox_mercator.ymax < 112000

def test_bounding_box_mercator_extreme_coordinates():
    """
    Extreme lat/lon values
    Verify:
    - Returned object is BoundingBoxMercator
    - xmin < xmax, ymin < ymax
    - No infinite values
    """
    user_input = UserInput(
        aoi_name = "test_aoi",
        sw_lat = -85,
        sw_lon = -179,
        ne_lat = 85,
        ne_lon = 179,
        resolution = 1,
        routing_source = 1,
        routing_target = 2,
        routing_weight = RoutingPreference.SHORTEST)

    bbox_mercator = bounding_box_mercator(user_input)

    assert isinstance(bbox_mercator, BoundingBoxMercator)

    assert bbox_mercator.xmin < bbox_mercator.xmax
    assert bbox_mercator.ymin < bbox_mercator.ymax

    for val in [bbox_mercator.xmin, bbox_mercator.ymin, bbox_mercator.xmax, bbox_mercator.ymax]:
        assert val != float("inf")

def test_tile_calculator_basic():
    '''
    ----------------------------------------
    Function: tile_calculator(bbox_mercator, resolution)
    ----------------------------------------
    # Normal cases
    # - Typical bbox and resolution -> check width and height
    # - Large bbox with reasonable resolution

    # Edge cases
    # - Zero resolution -> should raise ZeroDivisionError
    # - Negative resolution -> optional, decide expected behavior
    # - Very small bbox (width or height < 1 pixel) -> output should round correctly
    # - Very large bbox -> output should not overflow integer
    '''

    bbox_mercator = BoundingBoxMercator(
        xmin = 0,
        ymin = 0,
        xmax = 0,
        ymax = 0)
    resolution = 10

    width, height = tile_calculator(bbox_mercator, resolution)


#bounding_box_osm
#reproject_raster_layer

"""
----------------------------------------
Function: bounding_box_osm(user_input)
----------------------------------------
# Normal cases
# - Typical coordinates -> output tuple (xmin, ymin, xmax, ymax)
# - Verify ordering: left, bottom, right, top

# Edge cases
# - Degenerate bbox (SW == NE)
# - SW > NE coordinates

# Error cases
# - Missing or None values -> should raise AttributeError

----------------------------------------
Function: reproject_raster_layer(dst_crs, input_raster, output_raster)
----------------------------------------
# Normal cases
# - Small dummy raster -> output raster created
# - Verify CRS, width, height

# Edge cases
# - Empty raster -> should not crash
# - Unsupported CRS string -> should raise an error

# Error cases
# - input_raster path does not exist -> FileNotFoundError
# - output path permission denied -> PermissionError

----------------------------------------
Function: reproject_vector_layer(dst_crs, input_vector, output_vector)
----------------------------------------
# Normal cases
# - Small GeoDataFrame -> output file created
# - Verify CRS of output

# Edge cases
# - Empty GeoDataFrame
# - Invalid CRS string

# Error cases
# - input_vector path does not exist -> FileNotFoundError
# - output_vector path permission denied -> PermissionError

----------------------------------------
Function: raster_to_vector(input_raster_path, output_vector_path)
----------------------------------------
# Normal cases
# - Small raster mask with 255 pixels -> vector polygons created
# - Output file created

# Edge cases
# - Raster with no 255 pixels -> output GeoDataFrame empty
# - Single pixel raster -> produces single polygon
# - Large raster -> memory usage reasonable (can mock)

# Error cases
# - Input file does not exist -> FileNotFoundError
# - Output path permission denied -> PermissionError

----------------------------------------
Function: add_id(gdf, id_vector_path)
----------------------------------------
# Normal cases
# - GeoDataFrame with multiple features -> 'id' column added, starts at 1

# Edge cases
# - Empty GeoDataFrame -> 'id' column added (empty)
# - Existing 'id' column -> should overwrite or handle gracefully

# Error cases
# - Output path permission denied -> PermissionError

----------------------------------------
Function: buffer_vector(gdf, distance)
----------------------------------------
# Normal cases
# - Typical polygon -> buffered correctly
# - Line or point geometries -> buffered correctly

# Edge cases
# - Distance = 0 -> geometries unchanged
# - Negative distance -> optional behavior
# - Empty GeoDataFrame

# Error cases
# - Invalid geometry types -> should raise error

----------------------------------------
Function: clipping_vectors(input_vector, mask_vector, output_vector_path)
----------------------------------------
# Normal cases
# - Input polygon clipped by mask -> output matches expected
# - Output file created

# Edge cases
# - Input or mask empty -> output empty
# - No overlap between input and mask -> output empty
# - Partial overlap -> check geometry

# Error cases
# - Output path permission denied -> PermissionError

----------------------------------------
Function: calculate_area(gdf)
----------------------------------------
# Normal cases
# - Polygon geometries -> 'area' column added, positive values
# - Multipolygons -> areas sum correctly

# Edge cases
# - Empty GeoDataFrame -> 'area' column added (empty)
# - Degenerate polygons -> area = 0
# - Polygons with invalid geometries -> handled or fixed

# Error cases
# - Non-polygon geometries -> should raise error or skip

----------------------------------------
Function: join_by_attribute(gdf, join)
----------------------------------------
# Normal cases
# - Matching IDs -> area values merged
# - Non-matching IDs -> NaN or filled value

# Edge cases
# - Empty gdf or join -> returns empty or unchanged
# - Duplicate IDs in join -> behavior defined (merge strategy)

# Error cases
# - Missing 'id' column -> KeyError

----------------------------------------
Function: calculate_greendex(gdf)
----------------------------------------
# Normal cases
# - Normal area_x, area_y values -> greendex and weight calculated
# - Length normalization correct

# Edge cases
# - area_x = 0 -> greendex = 0
# - area_y > area_x -> greendex > 1 -> capped or handled
# - length min == max -> division by zero

# Error cases
# - Missing columns -> KeyError
# - Empty GeoDataFrame
"""
