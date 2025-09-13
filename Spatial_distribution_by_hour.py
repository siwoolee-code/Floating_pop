"""
Author: Siwoo
Description:
    This script calculates the 2022–2024 average hourly floating population
    for South Korea at 1 km resolution and visualizes the spatial distribution
    of Seoul and Busan for selected hours. Areas outside each city are shown
    in white. Scale bars and consistent color mapping are included.
"""

import os
import glob
import numpy as np
import rasterio
from rasterio import features
import geopandas as gpd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.anchored_artists import AnchoredSizeBar
import matplotlib.font_manager as fm
from tqdm import tqdm

# ─── 1) Paths and settings ─────────────────────────────────────────────
# User should set these paths
DATA_PATH = r'/path/to/floating_population_data'  # directory containing yearly GeoTIFFs
GRID_DIR = r'/path/to/city_grid_shapefiles'       # directory containing city shapefiles

CITIES = ['Seoul','Busan']
TARGET_HOURS = [4, 8, 13, 20]  # hours to visualize

FONT_PROPS = fm.FontProperties(size=8)

# ─── 2) Compute 2022–2024 hourly mean ─────────────────────────────────
all_sum = None
file_count = 0

for year in [2022, 2023, 2024]:
    tif_list = sorted(glob.glob(os.path.join(DATA_PATH, f'{year}/*.tif')))
    print(f"{year} - Total daily files: {len(tif_list)}")

    for tif_file in tqdm(tif_list, desc=f'Processing {year}'):
        with rasterio.open(tif_file) as src:
            data = src.read()  # shape = (24, H, W)
            if all_sum is None:
                all_sum = np.zeros_like(data, dtype=np.float64)
                transform_ref = src.transform
                H, W = data.shape[1], data.shape[2]
            all_sum += data
        file_count += 1

hourly_mean = all_sum / file_count
print("hourly_mean shape:", hourly_mean.shape)  # (24, H, W)

# ─── 3) Rasterize city shapefiles to hourly_mean shape ────────────────
city_masks = {}
for city in CITIES:
    shp_path = os.path.join(GRID_DIR, f"{city}_1km_grid.shp")
    gdf = gpd.read_file(shp_path).to_crs("EPSG:5179")
    
    shapes = ((geom, 1) for geom in gdf.geometry)
    city_mask = features.rasterize(
        shapes=shapes,
        out_shape=(H, W),
        transform=transform_ref,
        fill=0,
        dtype='uint8'
    )
    city_masks[city] = city_mask
    print(f"{city} mask shape: {city_mask.shape}, unique values: {np.unique(city_mask)}")

# ─── 4) Plot hourly spatial distribution ───────────────────────────────


for hr in TARGET_HOURS:
    print(f"\n🗺️ Visualizing Hour {hr:02d}:00 …")
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)

    for ax, city in zip(axes, CITIES):
        city_mask = city_masks[city]
        hr_data = hourly_mean[hr, :, :]

        # Crop to city's bounding box
        rows, cols = np.where(city_mask == 1)
        row_min, row_max = rows.min(), rows.max()
        col_min, col_max = cols.min(), cols.max()

        city_crop = hr_data[row_min:row_max+1, col_min:col_max+1]
        mask_crop = city_mask[row_min:row_max+1, col_min:col_max+1]

        # Set areas outside city to NaN (white)
        display_data = np.where(mask_crop==1, city_crop, np.nan)

        # Plot
        cmap = plt.cm.OrRd.copy()
        cmap.set_bad(color='white')  # NaN → white

        # Optional: fix color scale for all plots
        VMIN = 0
        VMAX = 50000
        im = ax.imshow(display_data, cmap=cmap, origin='upper', vmin=VMIN, vmax=VMAX)
        ax.set_title(f"{city} Hour {hr:02d}:00", fontsize=10)
        ax.axis('off')


    # Shared colorbar
    fig.colorbar(im, ax=axes, orientation='vertical', fraction=0.03, pad=0.02, label='Population')
    plt.show()
