from utils.paths import get_data_folder
from utils.geometry import reproject_raster_layer, reproject_vector_layer




# Reproject all layers to EPSG: 5070 for testing. Later it can change dynamically.

# Reproject satellite image
def reproject_naip_image():

    dst_crs = 'EPSG:5070'
    input_raster = get_data_folder("raw") + '/naip_test.tif'
    output_raster = get_data_folder("raw") + '/naip_test_reprojected.tif'
    print('INPUT RASTER PATH: ', input_raster)

    reproject_raster_layer(dst_crs, input_raster, output_raster)

# Reproject tree mask
def reproject_tree_mask():
    dst_crs = 'EPSG:5070'
    input_raster = 'C:/Users/balazs/urban-green-routing/data/raw/tree_mask.tif'
    output_raster = 'C:/Users/balazs/urban-green-routing/data/raw/tree_mask_reprojected.tif'

    reproject_raster_layer(dst_crs, input_raster, output_raster)

# Reproject edges
def reproject_osm_edges():
    dst_crs = 'EPSG:5070'
    input_vector = 'C:/Users/balazs/urban-green-routing/data/raw/edges.gpkg'
    output_vector = 'C:/Users/balazs/urban-green-routing/data/raw/edges_reprojected.gpkg'

    reproject_vector_layer(dst_crs, input_vector, output_vector)

if __name__ == "__main__":
    reproject_naip_image()
    reproject_tree_mask()
    reproject_osm_edges()