# Google World Streetv 15k (GWS15k) Dataset Creation Script

This repository contains the script used to create the **Google World Streetview 15k (GWS15k)** dataset. The GWS15k dataset consists of 15,000 images sourced from Google Street View, each paired with relevant metadata including GPS coordinates (latitude and longitude), headings, city name, and country name. This dataset is designed for computer vision tasks, including geo-localization, urban mapping, and image-based location recognition.

## Table of Contents

- [Overview](#overview)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Dataset Structure](#dataset-structure)
- [Metadata](#metadata)
- [Contributing](#contributing)
- [License](#license)

## Overview

This script automates the collection of images and metadata from Google Street View using the Google Maps API. It allows users to specify geographical parameters and retrieves Street View images from a range of global locations.

Key features:
- Downloads 15,000 Street View images.
- Saves associated metadata (latitude, longitude, headings, city name, country name).
- Stores the data in a structured format for easy access and fast lookup by image ID.

How the dataset is created:
1. Pick a country with probability based on surface area respective to total surface area of land on Earth
2. Pick a random city in that country
3. Pick a random coordinate within 5 km of the town/city

## Requirements

Before using this script, ensure you have the following:
- A **Google Cloud Platform** account with access to the **Google Maps API**.
- The **Street View Static API** enabled on your Google Cloud account.
- Python 3.7+ installed.
- The following Python packages:
  - `requests`
  - `pyyaml`
  - `h5py`
  - `tqdm` (for progress tracking)
  - `numpy`
  - `dataclasses`
  - `pillow`
  - `python-dotenv`

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/wp4032/gws15k.git
   cd gws15k
   ```

2. Set up your Google Maps API key:
   - Follow the steps in the [Google Maps API documentation](https://developers.google.com/maps/documentation) to get your API key.
   - Export your API key as an environment variable or directly modify the script configuration.

   ```bash
   GOOGLE_API_KEY=INSERTKEYHERE
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

To run the script and start generating the dataset, use the following command:

```bash
python gws15k.py
```

The script will download the images and metadata to the specified directory and display progress in the terminal.

## Dataset Structure

The dataset will be saved in a HDF5 file.

## Metadata

The `metadata.csv` file includes the following fields:

| Column Name  | Description                                |
|--------------|--------------------------------------------|
| image_id     | Unique identifier for each image           |
| city         | The name of the nearest city               |
| country      | The name of the country                    |
| lat          | Latitude of the image location             |
| lon          | Longitude of the image location            |
| heading      | The compass heading of the camera when the image was taken |
| images       | The images stored as numpy arrays          |

### Example:

| image_id  | city      | country   | headings                                 | lat         | lon          |
|-----------|-----------|-----------|------------------------------------------|-------------|--------------|
| image_0   | Cobija    | Bolivia   | [48.6722742965912,138.67227429659118]    | -11.0264039 | -68.7511483  |
| image_1   | Rawasari  | Indonesia | [222.3601926424811,312.36019264248114]   |  -7.5648521  | 108.8731069 |

## Contributing

If you would like to contribute to this project, feel free to submit a pull request. Contributions such as bug fixes, improvements, and additional features are welcome.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
