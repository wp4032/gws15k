import random

import time
import pickle
import requests
import os
import yaml
import h5py
from tqdm import tqdm
import numpy as np
from dataclasses import dataclass
from PIL import Image
from io import BytesIO
from typing import List, Tuple, Dict
from dotenv import load_dotenv
from utils import get_unique_column_values, read_csv

# __________________________________________________________________
# ___________________________ VARIABLES ____________________________
# __________________________________________________________________

load_dotenv()

with open('config.yaml', 'r') as file:
  config = yaml.safe_load(file)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

TOTAL_LAND_AREA = 129965453 # km^2

LAND_AREA_FILE = config['general']['land_area_file']
WORLD_CITIES_FILE = config['general']['world_cities_file']
COUNTRY_PROBABILITIES_FILE = config['general']['country_probabilities_file']
DATASET_SIZE = config['general']['dataset_size']
DATASET_FILETYPE = config['general']['hdf5']
HDF5_FILENAME = config['general']['hdf5_filename']
DEBUG_MODE = config['general']['debug_mode']

NUMBER_OF_CITIES = config['general']['number_of_cities']

IMAGE_WIDTH = config['image']['width']
IMAGE_HEIGHT = config['image']['height']
IMAGE_VIEWS = config['image']['views']
RANDOM_HEADING = config['image']['random_heading']
IMAGE_SHAPE = (IMAGE_WIDTH, IMAGE_HEIGHT, 3)

CHUNK_SIZE = 100
WATERMARK_HEIGHT = 22

@dataclass
class LocationData:
  country: str
  city: str
  lat: float
  lon: float
  image_lat: float
  image_lon: float
  headings: List[float]
  images: List[np.ndarray]

# __________________________________________________________________
# ________________________ HELPER FUNCTIONS ________________________
# __________________________________________________________________

def random_from_landarea() -> str:
  data = read_csv(COUNTRY_PROBABILITIES_FILE)

  return random.choices([country for country, _ in data], weights=[float(prob) for _, prob in data], k=1)[0]

def random_city_from_world_city(country: str, city_dict: Dict[str, List[str]]) -> str:
  if country not in city_dict:
    raise KeyError(f"Country '{country}' not found in the city dictionary.")
  
  # Filter cities for the given country
  cities = city_dict[country]
  
  if not cities:
    raise ValueError(f"No cities found for country '{country}'.")
  
  # Return a random city from the filtered list
  return random.choice(cities)

def gps_coord_from_city(city: str, coordinate_dict: Dict[str, Tuple[float, float]]) -> Tuple[float, float]:
  # Check if the city exists in the dictionary
  if city not in coordinate_dict:
    raise KeyError(f"City '{city}' not found in the coordinate dictionary.")
  
  return coordinate_dict[city]

def get_nearby_street_view_image(info_dict: LocationData, radius: int = 10000) -> List[str]:
    # Step 1: Find a nearby place or location using the Places API
    places_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    places_params = {
        'location': f"{info_dict['lat']},{info_dict['lon']}",
        'radius': radius,  # 5km radius
        'key': GOOGLE_API_KEY
    }

    response = requests.get(places_url, params=places_params)
    places_data = response.json()

    if not places_data.get('results'):
        raise ValueError("No places found within the specified radius.")
    
    # Step 2: Get the coordinates of the first nearby place
    random_index = random.randint(0, len(places_data['results']) - 1)
    random_place = places_data['results'][random_index]
    nearby_lat = random_place['geometry']['location']['lat']
    nearby_lon = random_place['geometry']['location']['lng']

    info_dict['image_lat'], info_dict['image_lon'] = nearby_lat, nearby_lon


    # Step 3: Use the Street View API to get the street view image for the nearby place
    street_view_url = f"https://maps.googleapis.com/maps/api/streetview"

    headings = {
        1: [0],            # Front view only
        2: [0, 90],        # Front and right
        3: [0, 90, 180],   # Front, right, and back
        4: [0, 90, 180, 270]  # Front, right, back, and left
    }

    # Validate image_views input
    if IMAGE_VIEWS not in headings:
        raise ValueError("IMAGE_VIEWS must be between 1 and 4.")

    # You can check the metadata of the Street View as well
    metadata_url = f"https://maps.googleapis.com/maps/api/streetview/metadata"
    metadata_params = {
        'location': f'{nearby_lat},{nearby_lon}',
        'key': GOOGLE_API_KEY
    }
    
    metadata_response = requests.get(metadata_url, params=metadata_params)
    metadata = metadata_response.json()

    if metadata['status'] != 'OK':
        raise ValueError(f"No street view available for location: ({nearby_lat}, {nearby_lon})")

    # Step 4: Return the Street View image URL
    image_urls = []
    dict_headings = []
    random_heading = random.uniform(0, 360) if RANDOM_HEADING else 0
    for heading in headings[IMAGE_VIEWS]:
      street_view_image_url = f"{street_view_url}?location={nearby_lat},{nearby_lon}&heading={random_heading + heading}&size={IMAGE_WIDTH}x{IMAGE_HEIGHT + WATERMARK_HEIGHT}&key={GOOGLE_API_KEY}"
      image_urls.append(street_view_image_url)
      dict_headings.append(random_heading + heading)
    info_dict['headings'] = dict_headings
    return image_urls


def get_random_street_view_image(city_dict: Dict[str, List[str]], coordinate_dict: Dict[str, Tuple[float, float]]) -> LocationData:
  ret_dict = {}
  while True:
    try:
      ret_dict['country'] = random_from_landarea()
      ret_dict['city'] = random_city_from_world_city(ret_dict['country'], city_dict)
      ret_dict['lat'], ret_dict['lon'] = gps_coord_from_city(ret_dict['city'], coordinate_dict)
      ret_dict['image_urls'] = get_nearby_street_view_image(ret_dict)
      _add_npimages_from_urls(ret_dict) if DATASET_FILETYPE else _save_images_from_urls(ret_dict, 'png')
      return ret_dict
    except (ValueError, KeyError) as e:
      if(DEBUG_MODE):
        print(f"Error occurred: {e}. Retrying...")

# __________________________________________________________________
# ________________________ HELPER FUNCTIONS ________________________
# __________________________________________________________________

def _get_city_dictionary() -> Dict[str, List[str]]:
  with open("city_dict.pkl", "rb") as file:
    return pickle.load(file)

def _get_coordinate_dictionary() -> Dict[str, Tuple[float, float]]:
  with open("city_dict_with_coords.pkl", "rb") as file:
    return pickle.load(file)

def _crop_image(image):
  image = Image.open(BytesIO(image))
  return image.crop((0, 0, IMAGE_WIDTH, IMAGE_HEIGHT))

def _save_image_from_url(response, tag: int, location_dict, filetype: str) -> None:
  cropped_image = _crop_image(response.content)
  
  # Check if the filetype is valid
  valid_filetypes = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff']
  if filetype.lower() not in valid_filetypes:
    raise ValueError(f"Invalid filetype: {filetype}. Supported types are: {', '.join(valid_filetypes)}")
  
  # Save the cropped image
  save_path = os.path.join(".", f"{location_dict['image_lat']}_{location_dict['image_lon']}_{tag}.{filetype}")
  cropped_image.save(save_path)
  print(f"Cropped image successfully saved to {save_path}")

def _save_jpg_from_url(response, tag: int, location_dict) -> None:
  _save_image_from_url(response, tag, location_dict, "jpg")

def _save_png_from_url(response, tag: int, location_dict) -> None:
  _save_image_from_url(response, tag, location_dict, "png")

def _save_images_from_urls(location_dict, filetype: str) -> None:
  i = 0
  for image_url in location_dict['image_urls']:
    try:
      # Send a GET request to the URL to retrieve the image
      response = requests.get(image_url, stream=True)

      # Check if the request was successful
      if response.status_code == 200:
        _save_jpg_from_url(response, i, filetype)
      else:
        print(f"Failed to retrieve image. Status code: {response.status_code}")
    except Exception as e:
      print(f"An error occurred while processing the image: {e}")
    i += 1

def _add_npimages_from_urls(location_dict) -> None:
  for image_url in location_dict['image_urls']:
    try:
      # Send a GET request to the URL to retrieve the image
      response = requests.get(image_url, stream=True)

      # Check if the request was successful
      if response.status_code == 200:
        pil_image = _crop_image(response.content)
        # Convert PIL Image to numpy array
        np_image = np.array(pil_image)
        
        # Ensure the image has the correct shape
        if np_image.shape != IMAGE_SHAPE:
          print(f"Warning: Image shape {np_image.shape} does not match expected shape {IMAGE_SHAPE}")
          np_image = np.resize(np_image, IMAGE_SHAPE)
        
        # Add the numpy array to the location_dict
        if 'images' not in location_dict:
          location_dict['images'] = []
        location_dict['images'].append(np_image)
      else:
        print(f"Failed to retrieve image. Status code: {response.status_code}")
    except Exception as e:
      print(f"An error occurred while processing the image: {e}")

def _add_to_hdf5(hdf5_filename, data_dict):
  with h5py.File(hdf5_filename, 'a') as hdf5_file:
    # Generate unique identifier for group
    image_id = f"image_{len(hdf5_file.keys())}"

    # Create a new group for data entry
    group = hdf5_file.create_group(image_id)

    # Add metadata as attributes to group
    group.attrs['country'] = data_dict['country']
    group.attrs['city'] = data_dict['city']
    group.attrs['lat'] = data_dict['image_lat']
    group.attrs['lon'] = data_dict['image_lon']
    group.attrs['headings'] = data_dict['headings']

    group.create_dataset('images', data=data_dict['images'], dtype='uint8')

def _create_dataset_h5py():
  city_dictionary = _get_city_dictionary()
  coordinate_dictionary = _get_coordinate_dictionary()

  for i in tqdm(range(DATASET_SIZE), desc="Creating dataset", unit="image"):
    location_dict = get_random_street_view_image(city_dictionary, coordinate_dictionary)
    _add_to_hdf5(HDF5_FILENAME, location_dict)         




if __name__ == "__main__":
  start = time.time()
  _create_dataset_h5py()
  end = time.time()
  print(f"Time taken: {end - start} seconds")
