# gee_processor.py
import ee
import requests
import uuid
import json
from pathlib import Path
from shapely.geometry import Polygon, mapping
import geopandas as gpd

# --- GEE AUTHENTICATION ---
try:
    ee.Initialize(project="ee-geeapi")
    print("Google Earth Engine initialized successfully with project 'ee-geeapi'.")
except ee.EEException as e:
    print(f"Authentication failed. Please run 'earthengine authenticate'. Error: {e}")
    exit()

# --- HELPER FUNCTIONS ---

def convert_to_2d(geometry):
    if geometry.has_z:
        new_coords = [(x, y) for x, y, _ in geometry.exterior.coords]
        return Polygon(new_coords)
    return geometry

def kml_path_to_ee_geometry(kml_path):
    gdf = gpd.read_file(kml_path, driver="KML")
    gdf["geometry"] = gdf["geometry"].apply(convert_to_2d)
    geojson = mapping(gdf["geometry"].iloc[0])
    geojson_clean = json.loads(json.dumps(geojson))
    return ee.Geometry(geojson_clean)

# --- NEW: LULC MASKING LOGIC (Translated from JS) ---

def get_tree_cover(aoi, year, scale=10):
    """
    Uses Dynamic World to create a mask of areas classified as 'trees'.
    """
    startDate = ee.Date(f'{year}-01-01')
    endDate = ee.Date(f'{year+1}-01-01')
    
    dw = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1") \
        .filterDate(startDate, endDate) \
        .filterBounds(aoi) \
        .select('label') \
        .mode() \
        .clip(aoi)

    # Class 1 in Dynamic World corresponds to 'trees'
    dw_tree_mask = dw.eq(1)
    return dw_tree_mask.selfMask().reproject('EPSG:4326', None, scale)

def lulc_mask_image(image, aoi, year):
    """
    Applies the tree cover mask to a given image.
    """
    mask = get_tree_cover(aoi, year)
    return image.updateMask(mask)

def get_annual_embedding(aoi, year=2024):
    start_date = ee.Date(f'{year}-01-01')
    end_date = start_date.advance(1, 'year')
    embedding_collection = ee.ImageCollection('GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL')
    annual_image = embedding_collection \
        .filterDate(start_date, end_date) \
        .filterBounds(aoi) \
        .first()
    return annual_image

# --- MAIN PROCESSING FUNCTION ---

def generate_stratification(kml_content: bytes, max_clusters: int, year: int = 2024):
    temp_dir = Path("data/temp")
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_kml_path = temp_dir / f"{uuid.uuid4()}.kml"
    
    results_list = []

    try:
        with open(temp_kml_path, 'wb') as f:
            f.write(kml_content)

        aoi = kml_path_to_ee_geometry(temp_kml_path)
        
        # --- MODIFICATION: Apply the LULC mask here ---
        s2_image = get_annual_embedding(aoi, year)
        s2_image_aoi = lulc_mask_image(s2_image, aoi, year)
        
        training_data = s2_image_aoi.sample(region=aoi, scale=10, numPixels=1000)
        bounds_ee = aoi.bounds()
        bounds_coords = bounds_ee.getInfo()['coordinates'][0]
        bounds_for_leaflet = [
            [bounds_coords[0][1], bounds_coords[0][0]],
            [bounds_coords[2][1], bounds_coords[2][0]]
        ]

        for k in range(2, max_clusters + 1):
            print(f"Generating stratification for {k} clusters...")
            
            clusterer = ee.Clusterer.wekaKMeans(k).train(
                features=training_data,
                inputProperties=s2_image_aoi.bandNames()
            )
            classified_image = s2_image_aoi.cluster(clusterer)
            
            palette = ['FF0000', '00FF00', '0000FF', 'FFFF00', 'FF00FF', '00FFFF']
            vis_params = {'min': 0, 'max': k - 1, 'palette': palette[:k]}
            
            visualized_image = classified_image.visualize(**vis_params)
            final_image = visualized_image.clip(aoi).reproject('EPSG:4326', None, 10)
            
            image_url = final_image.getThumbUrl({
                'region': bounds_coords,
                'format': 'png'
            })
            
            response = requests.get(image_url)
            response.raise_for_status()
                
            overlays_dir = Path("data/media/overlays")
            overlays_dir.mkdir(parents=True, exist_ok=True)
            image_filename = f"{uuid.uuid4()}.png"
            image_path = overlays_dir / image_filename
            
            with open(image_path, 'wb') as f:
                f.write(response.content)

            results_list.append({
                "image_path": f"/data/media/overlays/{image_filename}",
                "bounds": bounds_for_leaflet,
                "cluster_count": k
            })

        return results_list

    except Exception as e:
        print(f"An error occurred during GEE processing: {e}")
        raise e
    finally:
        if temp_kml_path.exists():
            temp_kml_path.unlink()
