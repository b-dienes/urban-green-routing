import pytest
from unittest.mock import patch
import geopandas as gpd
import pyogrio
from shapely.geometry import Polygon
from pyproj import CRS
import numpy as np
import rasterio
from rasterio.transform import from_origin
from utils.inputs import UserInput, RoutingPreference
from utils.geometry import (
    BoundingBoxMercator,
    bounding_box_mercator,
    tile_calculator,
    bounding_box_osm,
    reproject_raster_layer,
    reproject_vector_layer,
    raster_to_vector,
    add_id,
    buffer_vector,
    clipping_vectors)


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

def test_tile_calculator_normal_bbox():
    """
    Typical bounding box and resolution.

    Verify:
    - Returned width and height are integers
    - Width and height are computed correctly from bbox size and resolution
    """
    bbox_mercator = BoundingBoxMercator(
        xmin = 0,
        ymin = 0,
        xmax = 10,
        ymax = 10)
    resolution = 1

    width, height = tile_calculator(bbox_mercator, resolution)

    assert isinstance(width, int)
    assert isinstance(height, int)

    assert width == 10
    assert height == 10


@pytest.mark.parametrize(
    "xmax, ymax, expected_msg",
        [
            (0.1,0.1,"Width and height (pixel count) must be >= 1. Width: 0, height: 0"),
            (10000,10000, "Tile size too large: maximum allowed is 2500x2500 pixels. Width: 10000, height: 10000")
        ]
)
def test_tile_calculator_invalid_bbox_size(xmax, ymax, expected_msg):
    """
    Invalid bounding box sizes resulting in unusable tile dimensions.

    Verify:
    - A ValueError is raised when the resulting width or height is < 1 pixel
    - A ValueError is raised when the resulting width or height exceeds the maximum allowed size (2500*2500 pixels)
    - The error message matches the expected, user-facing message
    - Resolution constraints (minimum 0.6m for NAIP imagery) are validated upstream and are not tested here
    """
    bbox_mercator = BoundingBoxMercator(
            xmin = 0,
            ymin = 0,
            xmax = xmax,
            ymax = ymax)

    resolution = 1

    with pytest.raises(ValueError) as exc_info:
        tile_calculator(bbox_mercator, resolution)

    assert str(exc_info.value) == expected_msg

def test_bounding_box_osm_normal_coordinates():
    """
    Normal bounding box coordinates converted to an OSM-compatible tuple.

    Verify:
    - The returned object is a tuple
    - All values are floats
    - The ordering is correct: (xmin, ymin, xmax, ymax)
    - Typical SW < NE coordinates are handled correctly
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

    bbox_osm = bounding_box_osm(user_input)

    assert isinstance(bbox_osm, tuple)

    for val in bbox_osm:
        assert isinstance(val, float)
    
    assert bbox_osm == (user_input.sw_lon, user_input.sw_lat, user_input.ne_lon, user_input.ne_lat)

def test_bounding_box_osm_extreme_coordinates():
    """
    Extreme bounding box coordinates converted to an OSM-compatible tuple.

    Verify:
    - The returned object is a tuple
    - xmin < xmax, ymin < ymax
    - No value is infinite
    - Works with coordinates near valid extremes (-85 to 85 latitude, -179 to 179 longitude)
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

    bbox_osm = bounding_box_osm(user_input)

    assert isinstance(bbox_osm, tuple)

    assert bbox_osm[0] < bbox_osm[2]
    assert bbox_osm[1] < bbox_osm[3]

    for val in bbox_osm:
        assert val != float("inf")
        assert isinstance(val, float)

@pytest.fixture
def simple_raster(tmp_path):
    """
    Create a simple 1-band 10x10 raster with EPSG:4326 CRS for testing.

    Returns:
        Path: Path to the created raster file.
    """
    raster_path = tmp_path / "input.tif"

    data = np.ones((1, 10, 10), dtype=np.uint8)
    transform = from_origin(0, 10, 1, 1)  # top left corner is at: x=0,y=10, pixel size=1

    with rasterio.open(
        raster_path,
        "w",
        driver="GTiff",
        height=10,
        width=10,
        count=1,
        dtype=data.dtype,
        crs="EPSG:4326",
        transform=transform,
    ) as dst:
        dst.write(data)

    return raster_path

def test_reproject_raster_layer_creates_output(simple_raster, tmp_path):
    """
    Reproject a valid single-band raster to a target CRS and write the result to disk.

    Verify:
    - The output raster file is created
    - The output raster CRS matches the requested target CRS
    - The output raster has valid, non-zero dimensions
    - The number of bands is preserved from the input raster
    """
    dst_crs = 'EPSG:5070'
    output_raster = tmp_path / "output.tif"

    reproject_raster_layer(dst_crs, simple_raster, output_raster)

    assert output_raster.exists()

    with rasterio.open(output_raster) as dst:
        assert dst.crs.to_string() == dst_crs
        assert dst.width > 0
        assert dst.height > 0
        assert dst.count == 1 #1band

def test_reproject_raster_layer_missing_input(tmp_path):
    """
    Verify that reprojecting a raster with a missing input path raises a RasterioIOError.
    """
    input_raster = tmp_path / "missing.tif"
    output_raster = tmp_path / "output.tif"

    with pytest.raises(rasterio.errors.RasterioIOError):
        reproject_raster_layer('EPSG:5070', input_raster, output_raster)

def test_reproject_raster_layer_invalid_crs(simple_raster, tmp_path):
    """
    Verify that reprojecting a raster with an invalid CRS string
    raises an error (ValueError or CRSError depending on rasterio version).
    """
    output_raster = tmp_path / "output.tif"

    with pytest.raises((rasterio.errors.CRSError, ValueError)):
        reproject_raster_layer('EPSG:INVALID', simple_raster, output_raster)

def test_reproject_raster_layer_permission_denied(simple_raster, tmp_path):
    """
    Verify that attempting to write to a location with simulated permission denial raises a RasterioIOError.
    """
    output_raster = tmp_path / "no_write"

    with patch("rasterio.open", side_effect=rasterio.errors.RasterioIOError("Permission denied")):
        with pytest.raises(rasterio.errors.RasterioIOError):
            reproject_raster_layer('EPSG:5070', simple_raster, output_raster)

@pytest.fixture
def simple_gdf():
    gdf = gpd.GeoDataFrame({
        "geometry": [Polygon([(0,0),(1,0),(1,1),(0,1)])]},
        geometry="geometry",
        crs="EPSG:4326")
    return gdf

@pytest.fixture
def empty_gdf():
    gdf = gpd.GeoDataFrame({
        "geometry": []},
        geometry="geometry",
        crs="EPSG:4326")
    return gdf

def test_reproject_vector_layer_creates_output(simple_gdf, tmp_path):
    """
    Reproject a small, valid GeoDataFrame to a target CRS and write the result to a GeoPackage.

    Verify:
    - The output vector file is created
    - The output vector CRS matches the requested target CRS
    """
    dst_crs = "EPSG:5070"
    input_vector = tmp_path / "input.gpkg"
    output_vector = tmp_path / "output.gpkg"

    simple_gdf.to_file(input_vector, driver="GPKG")

    reproject_vector_layer(dst_crs, input_vector, output_vector)

    assert output_vector.exists()

    out_gdf = gpd.read_file(output_vector)
    assert out_gdf.crs == CRS.from_user_input(dst_crs)

def test_reproject_vector_layer_allows_empty_vector(empty_gdf, tmp_path):
    """
    Reproject an empty GeoDataFrame to a target CRS and write the result to a GeoPackage.

    Verify:
    - The output vector file is created
    - The output vector contains zero features
    - The output vector CRS matches the requested target CRS
    """
    dst_crs = "EPSG:5070"
    input_vector = tmp_path / "input.gpkg"
    output_vector = tmp_path / "output.gpkg"

    empty_gdf.to_file(input_vector, driver="GPKG")

    reproject_vector_layer(dst_crs, input_vector, output_vector)

    out_gdf = gpd.read_file(output_vector)

    assert output_vector.exists()
    assert len(out_gdf) == 0
    assert out_gdf.crs == CRS.from_user_input(dst_crs)

def test_reproject_vector_layer_missing_input(tmp_path):
    """
    Attempt to reproject a vector file from a path that does not exist.

    Verify:
    - The function raises an appropriate exception (DataSourceError or ValueError)
    """
    input_vector = tmp_path / "missing.gpkg"
    output_vector = tmp_path / "output.gpkg"

    with pytest.raises((pyogrio.errors.DataSourceError, ValueError)):
        reproject_vector_layer('EPSG:5070', input_vector, output_vector)

def test_reproject_vector_layer_permission_denied(simple_gdf, tmp_path):
    """
    Attempt to reproject a valid GeoDataFrame to an output location with simulated write permission denial.

    Verify:
    - The function raises a PermissionError when writing the output file fails
    """
    input_vector = tmp_path / "input.gpkg"
    output_vector = tmp_path / "output.gpkg"

    simple_gdf.to_file(input_vector, driver="GPKG")

    with patch("geopandas.GeoDataFrame.to_file", side_effect=PermissionError("Permission denied")):
        with pytest.raises(PermissionError):
            reproject_vector_layer('EPSG:5070', input_vector, output_vector)


@pytest.fixture
def clustered_raster(tmp_path):
    """
    Create a 1-band 10x10 raster with two foreground clusters for testing.

    Returns:
        Path: Path to the created raster file.
    """
    raster_path = tmp_path / "clustered.tif"

    data = np.zeros((1, 10, 10), dtype=np.uint8)

    # Cluster 1 (top-left 3x3)
    data[0, 1:4, 1:4] = 255

    # Cluster 2 (bottom-right 3x3)
    data[0, 6:9, 6:9] = 255

    transform = from_origin(
        west=0,
        north=10,
        xsize=1,
        ysize=1,
    )

    with rasterio.open(
        raster_path,
        "w",
        driver="GTiff",
        height=10,
        width=10,
        count=1,
        dtype=data.dtype,
        crs="EPSG:5070",
        transform=transform,
        nodata=0,
    ) as dst:
        dst.write(data)

    return raster_path

def test_raster_to_vector_creates_output(clustered_raster, tmp_path):
    """
    Convert a raster mask with multiple foreground clusters into vector polygons.

    Verify:
    - The output GeoPackage file is created
    - Two vector features are produced, corresponding to the two raster clusters
    - The output CRS matches the input raster CRS
    - All geometries are valid and non-degenerate
    - The polygon areas match the expected raster cluster size
    """
    output_vector_path =tmp_path / "output.gpkg"

    raster_to_vector(clustered_raster, output_vector_path)

    assert output_vector_path.exists()

    out_gdf = gpd.read_file(output_vector_path)
    assert len(out_gdf) == 2
    assert out_gdf.crs.to_string() == "EPSG:5070"
    assert all(out_gdf.geometry.is_valid)

    areas = sorted(out_gdf.geometry.area)
    assert areas[0] == pytest.approx(9.0)
    assert areas[1] == pytest.approx(9.0)

@pytest.fixture
def one_pixel_raster(tmp_path):
    """
    Create a 1-band 1x1 raster with a single foreground pixel for testing.

    Returns:
        Path: Path to the created raster file.
    """
    raster_path = tmp_path / "input.tif"

    data = np.full((1, 1, 1), 255, dtype=np.uint8)
    transform = from_origin(0, 1, 1, 1)  # top left corner is at: x=0,y=1, pixel size=1

    with rasterio.open(
        raster_path,
        "w",
        driver="GTiff",
        height=1,
        width=1,
        count=1,
        dtype=data.dtype,
        crs="EPSG:5070",
        transform=transform,
    ) as dst:
        dst.write(data)

    return raster_path

def test_raster_to_vector_single_output(one_pixel_raster, tmp_path):
    """
    Convert a single-pixel foreground raster into a vector polygon.

    Verify:
    - The output GeoPackage file is created
    - Exactly one vector feature is produced
    - The resulting polygon has the expected area corresponding to one raster pixel
    """
    output_vector_path = tmp_path / "output.gpkg"

    raster_to_vector(one_pixel_raster, output_vector_path)

    assert output_vector_path.exists()

    out_gdf = gpd.read_file(output_vector_path)
    assert len(out_gdf) == 1

    geom = out_gdf.geometry.iloc[0]
    assert geom.area == pytest.approx(1.0)

def test_raster_to_vector_incorrect_grayscale_value(simple_raster, tmp_path):
    """
    Attempt raster-to-vector conversion on a raster with no valid foreground pixels.

    Verify:
    - A ValueError is raised when no pixels with value=255 are present
    - The error message clearly indicates the absence of foreground pixels
    """
    output_vector_path = tmp_path / "output.gpkg"

    with pytest.raises(ValueError) as exc_info:
        raster_to_vector(simple_raster, output_vector_path)

    expected_msg = "No foreground pixels (value=255) found in raster"
    assert str(exc_info.value) == expected_msg

def test_raster_to_vector_missing_input(tmp_path):
    """
    Attempt raster-to-vector conversion using a non-existent input raster file.

    Verify:
    - An exception is raised when the input raster path does not exist
    - The function does not create any output files when input reading fails
    """
    input_raster_path = tmp_path / "missing.tif"
    output_vector_path = tmp_path / "output.gpkg"

    with pytest.raises((rasterio.errors.RasterioIOError, ValueError)):
        raster_to_vector(input_raster_path, output_vector_path)


def test_raster_to_vector_permission_denied(one_pixel_raster, tmp_path):
    """
    Attempt to write vector output to a location without write permissions.

    Verify:
    - A PermissionError is raised when the output GeoPackage cannot be written
    - The error originates from the vector file writing stage
    """
    output_vector_path = tmp_path / "no_write"

    with patch("geopandas.GeoDataFrame.to_file", side_effect=PermissionError("Permission denied")):
        with pytest.raises(PermissionError):
            raster_to_vector(one_pixel_raster, output_vector_path)

@pytest.fixture
def complex_gdf():
    gdf = gpd.GeoDataFrame({
        "geometry": [
            Polygon([(0,0),(1,0),(1,1),(0,1)]),
            Polygon([(3,3),(4,0),(4,4),(0,4)]),
            Polygon([(5,5),(6,0),(6,6),(0,6)])]},
        geometry="geometry",
        crs="EPSG:5070")
    return gdf

def test_add_id_adds_id(complex_gdf, tmp_path):
    """
    Add a unique integer ID column to a GeoDataFrame and verify the result.

    Verify:
    - The output GeoPackage file is created
    - The number of features is unchanged
    - The 'id' column exists and contains sequential integers starting at 1
    """
    id_vector_path = tmp_path / "output.gpkg"

    add_id(complex_gdf, id_vector_path)

    assert id_vector_path.exists()

    out_gdf = gpd.read_file(id_vector_path)
    assert len(out_gdf) == len(complex_gdf)

    assert "id" in out_gdf.columns

    expected_ids = list(range(1,len(complex_gdf)+1))
    assert out_gdf['id'].tolist() == expected_ids

def test_add_id_empty_vector(empty_gdf, tmp_path):
    """
    Add a unique integer ID column to an empty GeoDataFrame.

    Verify:
    - The output GeoPackage file is created
    - The resulting GeoDataFrame has zero rows
    - The 'id' column exists even if empty
    """
    id_vector_path = tmp_path / "output.gpkg"

    add_id(empty_gdf, id_vector_path)

    assert id_vector_path.exists()

    out_gdf = gpd.read_file(id_vector_path)
    assert len(out_gdf) == 0
    assert "id" in out_gdf.columns

def test_add_id_existing_id_field(complex_gdf, tmp_path):
    """
    Add a unique integer ID column to a GeoDataFrame that already has an 'id' column.

    Verify:
    - The output GeoPackage file is created
    - The number of features is unchanged
    - The 'id' column is overwritten with sequential integers starting at 1
    """
    id_vector_path = tmp_path / "output.gpkg"

    gdf_with_id = complex_gdf.copy()
    gdf_with_id['id'] = range(len(gdf_with_id), 0, -1)

    add_id(gdf_with_id, id_vector_path)

    assert id_vector_path.exists()

    out_gdf = gpd.read_file(id_vector_path)
    assert len(out_gdf) == len(gdf_with_id)

    expected_ids = list(range(1,len(complex_gdf)+1))
    assert out_gdf['id'].tolist() == expected_ids

def test_add_id_permission_denied(simple_gdf, tmp_path):
    """
    Attempt to write a GeoDataFrame to a location without write permissions.

    Raises:
        PermissionError: If the output file cannot be written due to insufficient permissions.
    """
    id_vector_path = tmp_path / "no_write"

    with patch("geopandas.GeoDataFrame.to_file", side_effect=PermissionError("Permission denied")):
        with pytest.raises(PermissionError):
            add_id(simple_gdf, id_vector_path)

def test_buffer_vector_creates_buffer(simple_gdf):
    """
    Create a buffer around a valid polygon geometry.

    Verify:
    - A GeoDataFrame is returned
    - The number of features remains unchanged
    - All output geometries are valid
    - The buffered geometries have a larger area than the original geometries
    """
    distance = 1

    out_gdf = buffer_vector(simple_gdf, distance)

    assert out_gdf is not None
    assert len(out_gdf) == len(simple_gdf)
    assert all(out_gdf.geometry.is_valid)
    assert all(out_gdf.geometry.area > simple_gdf.geometry.area)

def test_buffer_vector_empty_buffer(empty_gdf):
    """
    Apply buffering to an empty GeoDataFrame.

    Verify:
    - A GeoDataFrame is returned
    - The output GeoDataFrame contains no features
    """
    distance = 1

    out_gdf = buffer_vector(empty_gdf, distance)

    assert out_gdf is not None
    assert len(out_gdf) == 0

def test_buffer_vector_invalid_distance(simple_gdf):
    """
    Attempt to create a buffer using a non-positive distance.

    Raises:
        ValueError: If the buffer distance is zero or negative.
    """
    distance = 0

    with pytest.raises(ValueError) as exc_info:
        buffer_vector(simple_gdf, distance)

    expected_msg = "Invalid buffer distance"
    assert str(exc_info.value) == expected_msg

def test_buffer_vector_invalid_geometry():
    """
    Attempt to buffer a GeoDataFrame containing invalid geometries.

    Raises:
        ValueError: If the input GeoDataFrame contains geometries that are not valid.
    """
    poly = Polygon([(0,0),(1,1),(1,0),(0,1),(0,0)])
    invalid_gdf = gpd.GeoDataFrame({"geometry": [poly]}, geometry="geometry")

    with pytest.raises(ValueError) as exc_info:
        buffer_vector(invalid_gdf, 1)

    expected_msg = "Input contains invalid geometries"
    assert str(exc_info.value) == expected_msg

def test_buffer_vector_none_geometry():
    """
    Attempt to buffer a GeoDataFrame containing null geometries.

    Raises:
        ValueError: If the input GeoDataFrame contains null geometry values.
    """
    gdf = gpd.GeoDataFrame({"geometry": [None]}, geometry="geometry")

    with pytest.raises(ValueError) as exc_info:
        buffer_vector(gdf, 1)

    expected_msg = "Input contains null geometries"
    assert str(exc_info.value) == expected_msg

@pytest.fixture
def mask_gdf():
    gdf = gpd.GeoDataFrame({
        "geometry": [Polygon([(0.5,0),(1.5,0),(1.5,1),(0.5,1)])]},
        geometry="geometry",
        crs="EPSG:4326")
    return gdf

@pytest.fixture
def mask_gdf_epsg_5070():
    gdf = gpd.GeoDataFrame({
        "geometry": [Polygon([(0.5,0),(1.5,0),(1.5,1),(0.5,1)])]},
        geometry="geometry",
        crs="EPSG:5070")
    return gdf


@pytest.fixture
def invalid_gdf():
    gdf = gpd.GeoDataFrame({
        "geometry": [Polygon([(0,0),(1,1),(1,0),(0,1),(0,0)])]},
        geometry="geometry",
        crs="EPSG:4326")
    return gdf

@pytest.fixture
def none_gdf():
    gdf = gpd.GeoDataFrame({
        "geometry": [None]},
        geometry="geometry",
        crs="EPSG:4326")
    return gdf

def test_clipping_vectors_creates_clip(simple_gdf, mask_gdf, tmp_path):
    """
    Clip a simple input polygon using a mask polygon and write the result to disk.

    Verify:
    - The output vector file is created
    - The output CRS matches the input CRS
    - The resulting geometry is valid
    - The clipped geometry has the expected area
    """
    output_vector_path = tmp_path / "output.gpkg"

    clipping_vectors(simple_gdf, mask_gdf, output_vector_path)

    assert output_vector_path.exists()

    out_gdf = gpd.read_file(output_vector_path)
    assert out_gdf.crs == simple_gdf.crs
    assert all(out_gdf.geometry.is_valid)
    assert pytest.approx(out_gdf.area.iloc[0]) == simple_gdf.area.iloc[0] * 0.5

def test_clipping_vectors_crs_mismatch(simple_gdf, mask_gdf_epsg_5070, tmp_path):
    """
    Attempt to clip vectors with mismatching coordinate reference systems.

    Raises:
        ValueError: If the input and mask GeoDataFrames have different CRS.
    """
    output_vector_path = tmp_path / "output.gpkg"

    with pytest.raises(ValueError) as exc_info:
        clipping_vectors(simple_gdf, mask_gdf_epsg_5070, output_vector_path)

    expected_msg = "Input and mask CRS must match"
    assert str(exc_info.value) == expected_msg

def test_clipping_vectors_empty_input(simple_gdf, empty_gdf, tmp_path):
    """
    Clip a valid input GeoDataFrame using an empty mask.

    Verify:
    - The output vector file is created
    - The resulting GeoDataFrame is empty
    """
    output_vector_path = tmp_path / "output.gpkg"

    clipping_vectors(simple_gdf, empty_gdf, output_vector_path)

    assert output_vector_path.exists()

    out_gdf = gpd.read_file(output_vector_path)
    assert out_gdf is not None
    assert len(out_gdf) == 0

def test_clipping_vectors_invalid_input_geometry(invalid_gdf, simple_gdf, tmp_path):
    """
    Attempt to clip vectors when the input GeoDataFrame contains invalid geometries.

    Raises:
        ValueError: If the input GeoDataFrame contains invalid geometries.
    """
    output_vector_path = tmp_path / "output.gpkg"

    with pytest.raises(ValueError) as exc_info:
        clipping_vectors(invalid_gdf, simple_gdf, output_vector_path)

    expected_msg = "Input contains invalid geometries"
    assert str(exc_info.value) == expected_msg

def test_clipping_vectors_invalid_mask_geometry(simple_gdf, invalid_gdf, tmp_path):
    """
    Attempt to clip vectors when the mask GeoDataFrame contains invalid geometries.

    Raises:
        ValueError: If the mask GeoDataFrame contains invalid geometries.
    """
    output_vector_path = tmp_path / "output.gpkg"

    with pytest.raises(ValueError) as exc_info:
        clipping_vectors(simple_gdf, invalid_gdf, output_vector_path)

    expected_msg = "Mask contains invalid geometries"
    assert str(exc_info.value) == expected_msg

def test_clipping_vectors_none_input_geometry(simple_gdf, none_gdf, tmp_path):
    """
    Attempt to clip vectors when the input GeoDataFrame contains null geometries.

    Raises:
        ValueError: If the input GeoDataFrame contains null geometries.
    """
    output_vector_path = tmp_path / "output.gpkg"

    with pytest.raises(ValueError) as exc_info:
        clipping_vectors(none_gdf, simple_gdf, output_vector_path)

    expected_msg = "Input contains null geometries"
    assert str(exc_info.value) == expected_msg

def test_clipping_vectors_none_mask_geometry(simple_gdf, none_gdf, tmp_path):
    """
    Attempt to clip vectors when the mask GeoDataFrame contains null geometries.

    Raises:
        ValueError: If the mask GeoDataFrame contains null geometries.
    """
    output_vector_path = tmp_path / "output.gpkg"

    with pytest.raises(ValueError) as exc_info:
        clipping_vectors(simple_gdf, none_gdf, output_vector_path)

    expected_msg = "Mask contains null geometries"
    assert str(exc_info.value) == expected_msg

def test_clipping_vectors_permission_denied(simple_gdf, mask_gdf, tmp_path):
    """
    Attempt to write clipped vector output to a location without write permissions.

    Verify:
    - A PermissionError is raised when the output GeoPackage cannot be written
    - The error originates from the vector file writing stage
    """
    output_vector_path = tmp_path / "no_write"

    with patch("geopandas.GeoDataFrame.to_file", side_effect=PermissionError("Permission denied")):
        with pytest.raises(PermissionError):
            clipping_vectors(simple_gdf, mask_gdf, output_vector_path)


"""
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
