#!/usr/bin/env python3
"""
convert_shp_to_geojson.py
─────────────────────────
Downloads the official Elections Canada federal electoral districts shapefile,
converts it to GeoJSON (WGS84), and saves it as federal_electoral_districts.geojson
in the same folder as this script.

Usage:
    pip install geopandas requests
    python3 convert_shp_to_geojson.py

The output file should be placed in the same folder as canada-election-modeller.html,
then served with:
    python3 -m http.server 8080
"""

import os
import sys
import zipfile
import io
import requests
import geopandas as gpd

# ── Elections Canada shapefile URL ────────────────────────────────────────
SHAPEFILE_URL = 'https://www.elections.ca/res/cir/mapsCorner/vector/FederalElectoralDistricts_2025_SHP.zip'

OUTPUT_FILE = 'federal_electoral_districts.geojson'


def main():
    print('Canadian Electoral Districts — Shapefile to GeoJSON Converter')
    print('=' * 60)

    # ── Step 1: Download ──────────────────────────────────────────────────
    print(f'\n[1/3] Downloading Elections Canada shapefile (~25 MB)...')

    try:
        r = requests.get(SHAPEFILE_URL, timeout=120, stream=True)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f'\nERROR: Could not download shapefile: {e}')
        sys.exit(1)

    total = int(r.headers.get('content-length', 0))
    downloaded = 0
    chunks = []
    for chunk in r.iter_content(chunk_size=65536):
        chunks.append(chunk)
        downloaded += len(chunk)
        if total:
            pct = downloaded / total * 100
            print(f'\r      {downloaded/1e6:.1f} MB / {total/1e6:.1f} MB ({pct:.0f}%)', end='', flush=True)
    print()
    zip_bytes = b''.join(chunks)
    print('      Download complete.')

    # ── Step 2: Extract and load shapefile ───────────────────────────────
    print('\n[2/3] Extracting and loading shapefile...')

    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        shp_files = [f for f in z.namelist() if f.endswith('.shp')]
        if not shp_files:
            print('ERROR: No .shp file found in the downloaded zip.')
            sys.exit(1)
        print(f'      Found: {shp_files[0]}')
        extract_dir = 'fed_shp_tmp'
        z.extractall(extract_dir)

    shp_path = os.path.join(extract_dir, shp_files[0])
    gdf = gpd.read_file(shp_path)
    print(f'      Loaded {len(gdf)} electoral districts.')
    print(f'      CRS: {gdf.crs}')

    # ── Step 3: Reproject to WGS84 and export ────────────────────────────
    print('\n[3/3] Reprojecting to WGS84 and saving GeoJSON...')

    gdf = gdf.to_crs('EPSG:4326')
    gdf.to_file(OUTPUT_FILE, driver='GeoJSON')

    size_mb = os.path.getsize(OUTPUT_FILE) / 1e6
    print(f'      Saved: {OUTPUT_FILE} ({size_mb:.1f} MB)')

    import shutil
    shutil.rmtree(extract_dir, ignore_errors=True)

    print('\n' + '=' * 60)
    print('Done! Now serve the files with:')
    print('  python3 -m http.server 8080')
    print('Then open:')
    print('  http://localhost:8080/canada-election-modeller.html')


if __name__ == '__main__':
    main()
