"""
Author: Siwoo
Description:
This script demonstrates how to compute and visualize nationwide floating population differences
between specific hours using high-resolution (1 km) GeoTIFF datasets.

"""

import os
import glob
import numpy as np
import rasterio
from rasterio.warp import calculate_default_transform, reproject, Resampling
import matplotlib.pyplot as plt
from tqdm import tqdm

# -----------------------------
# 1. Set paths and list TIF files
# -----------------------------

FP_tif_files = sorted(glob.glob(r'.../*.tif')))
print(f"Total TIF files: {len(FP_tif_files)}")

# -----------------------------
# 2. Define hours to read (04:00, 13:00)
# rasterio uses 1-based indexing
# -----------------------------
hours_to_read = [5, 14]  # 04:00 -> band 5, 13:00 -> band 14

data_04 = []
data_13 = []

for f in tqdm(FP_tif_files, desc="Reading TIF files"):
    with rasterio.open(f) as src:
        # Reproject to EPSG:4326
        dst_crs = "EPSG:4326"
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds
        )
        
        band_04 = np.empty((height, width), dtype=src.dtypes[0])
        band_13 = np.empty((height, width), dtype=src.dtypes[0])

        reproject(
            source=src.read(hours_to_read[0]),
            destination=band_04,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs=dst_crs,
            resampling=Resampling.nearest
        )
        reproject(
            source=src.read(hours_to_read[1]),
            destination=band_13,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=transform,
            dst_crs=dst_crs,
            resampling=Resampling.nearest
        )

        data_04.append(band_04)
        data_13.append(band_13)

# -----------------------------
# 3. Convert lists to numpy arrays and calculate mean
# -----------------------------
data_04 = np.array(data_04)
data_13 = np.array(data_13)

avg_04 = data_04.mean(axis=0)
avg_13 = data_13.mean(axis=0)
diff_avg = avg_04 - avg_13
print("diff_avg shape:", diff_avg.shape)

# -----------------------------
# 4. Visualization (EPSG:4326)
# -----------------------------
vmin, vmax = -2000, 2000

# Compute extent for imshow: [left, right, bottom, top] in lon/lat
extent = [
    transform[2], transform[2] + transform[0]*width,  # left, right
    transform[5] + transform[4]*height, transform[5]  # bottom, top
]

# Map limits covering South Korea (including Jeju)
lon_min, lon_max = 125.7, 129.7
lat_min, lat_max = 33.0, 38.7

fig, ax = plt.subplots(figsize=(10, 10))

# Plot difference map
im = ax.imshow(diff_avg, cmap='bwr', vmin=vmin, vmax=vmax, extent=extent, origin='upper')

# Add colorbar
cbar = plt.colorbar(im, ax=ax, fraction=0.036, pad=0.04, ticks=[-2000, 2000])
# cbar.set_label('04:00 - 13:00 difference')

# Set axes labels, limits, and ticks
ax.set_xlabel('Longitude')
ax.set_ylabel('Latitude')
ax.set_xlim(lon_min, lon_max)
ax.set_ylim(lat_min, lat_max)
ax.set_xticks([126, 127, 128, 129])
ax.set_yticks([34, 35, 36, 37, 38])

plt.tight_layout()
plt.show()
