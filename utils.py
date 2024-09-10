import csv
import yaml
import pickle
from typing import List, Tuple, Dict


with open('config.yaml', 'r') as file:
  config = yaml.safe_load(file)

LAND_AREA_FILE = config['general']['land_area_file']
WORLD_CITIES_FILE = config['general']['world_cities_file']
TOTAL_LAND_AREA = 129965453 # km^2
COUNTRY_PROBABILITIES_FILE = config['general']['country_probabilities_file']

def read_csv(file_path: str) -> List[List[str]]:
    with open(file_path, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        return list(reader)

def get_unique_column_values(file_path: str, column_index: int) -> List[str]:
    data = read_csv(file_path)
    return sorted(set(row[column_index] for row in data[1:] if len(row) > column_index))

def _get_csv_random_from_landarea() -> None:
  data = read_csv(LAND_AREA_FILE)

  # Extract header and find the index for 2021 data
  header = data[0]
  year_2021_index = header.index("2021")

  # Extract country names and 2021 land areas, skipping header
  countries_and_areas = [(row[0], float(row[year_2021_index])) for row in data[1:] if row[year_2021_index]]

  # Normalize probabilities
  probabilities = [area / TOTAL_LAND_AREA for _, area in countries_and_areas]

  # Create a list of tuples with country names and their probabilities
  country_probabilities = [(country, prob) for country, prob in zip([country for country, _ in countries_and_areas], probabilities)]
  
  # Sort the list by probability in descending order
  country_probabilities.sort(key=lambda x: x[1], reverse=True)
  
  # Write the probabilities to a CSV file
  with open(COUNTRY_PROBABILITIES_FILE, "w", newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerows(country_probabilities)
  
  return country_probabilities

def _make_city_dictionary() -> Dict[str, List[str]]:
  with open(WORLD_CITIES_FILE, "r", encoding="utf-8") as file:
    reader = csv.reader(file)
    data = list(reader)

  city_dict = {}
  for row in data[1:]:
    country = row[4]
    city = row[0]
    if country not in city_dict:
      city_dict[country] = []
    city_dict[country].append(city)

  return city_dict

def _make_city_dictionary_with_coords() -> Dict[str, Tuple[float, float]]:
    with open(WORLD_CITIES_FILE, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        data = list(reader)

    city_dict = {}
    for row in data[1:]:
        city = row[0]
        lat = float(row[2])
        lon = float(row[3])
        city_dict[city] = (lat, lon)

    return city_dict

def _get_countries_from_landarea() -> List[str]:
  return get_unique_column_values(LAND_AREA_FILE, 0)

def _get_countries_from_worldcities() -> List[str]:
  return get_unique_column_values(WORLD_CITIES_FILE, 4)

def _compare_countries_list(list1: List[str], list2: List[str]) -> List[str]:
  return sorted(set(list1) - set(list2))

def _export_city_dictionary_pickle() -> None:
  with open("city_dict.pkl", "wb") as file:
    pickle.dump(_make_city_dictionary(), file)

def _export_city_dictionary_with_coords_pickle() -> None:
  with open("city_dict_with_coords.pkl", "wb") as file:
    pickle.dump(_make_city_dictionary_with_coords(), file)
