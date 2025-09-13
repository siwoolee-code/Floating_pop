"""
Author: Siwoo
Description:
City-level Floating Population Visualization Example

This example demonstrates how to use an external city boundary shapefile (e.g., from OpenStreetMap)
with our 1 km-resolution floating population GeoTIFFs (EPSG:5179). 

The code:
1. Loads the city boundary shapefile.
2. Transforms its CRS to match our GeoTIFFs.
3. Clips a floating population raster to the city boundary.
4. Visualizes the result.
"""


import glob
import numpy as np
import geopandas as gpd
import rasterio
from rasterio import mask
import matplotlib.pyplot as plt

# -----------------------------
# User-defined paths
# -----------------------------
# Path to the city boundary shapefile (downloaded from OpenStreetMap or other GIS source)
city_boundary_path = r'path_to_your_city_boundary/city_boundary.shp'

# Path to the floating population GeoTIFF folder
data_path = r'path/to/floating_population_data/year'

# -----------------------------
# Load and transform city boundary
# -----------------------------
city_gdf = gpd.read_file(city_boundary_path)
# Transform CRS to match FP GeoTIFF (EPSG:5179)
city_gdf = city_gdf.to_crs("EPSG:5179")

# -----------------------------
# Select one FP GeoTIFF (0:00 hour)
# -----------------------------
tif_files = sorted(glob.glob(os.path.join(data_path, '*.tif')))
if not tif_files:
    raise FileNotFoundError(f"No TIF files found in {data_path}")

sample_tif = tif_files[0]  # first available date

with rasterio.open(sample_tif) as src:
    fp_data = src.read(1)  # Band 1 corresponds to 00:00
    fp_meta = src.meta.copy()

# -----------------------------
# Clip FP raster to city boundary
# -----------------------------
city_shapes = [geom for geom in city_gdf.geometry]  # list of shapely geometries

with rasterio.open(sample_tif) as src:
    fp_city, city_transform = mask.mask(src, city_shapes, crop=True)
    fp_city = fp_city[0]  # mask returns (bands, height, width)

# -----------------------------
# Visualization
# -----------------------------
plt.figure(figsize=(8,8))
plt.imshow(fp_city, cmap='OrRd', origin='upper')
plt.title('City-level Floating Population at 00:00 (Clipped)')
plt.colorbar(label='Population')
plt.axis('off')
plt.show()