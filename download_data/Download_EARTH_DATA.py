# %% This code is required at the beginning of the script to locate other modules
import os
import sys
# Get the current working directory and add root directory to path if run directly
current_directory = os.getcwd()
if current_directory.endswith("download_data"):
    sys.path.append(os.path.abspath(os.path.join(current_directory, "..")))
else:
    sys.path.append(current_directory)

# %%
from os.path import join
import datetime
from io_utils.io_common import create_folder, dotdict
import earthaccess

# %% 
"""
This program downloads data using NASA's earthaccess library.
https://earthaccess.readthedocs.io/en/stable/

Prerequisites:
    pip install earthaccess

Authentication:
    To authenticate, you need a free account at https://urs.earthdata.nasa.gov/
    The earthaccess library will automatically find your credentials if you set
    the environment variables EARTHDATA_USERNAME and EARTHDATA_PASSWORD,
    or if you have a .netrc file in your home directory with the format:

    machine urs.earthdata.nasa.gov
        login <username>
        password <password>

    If no credentials are found, it will prompt you interactively on the first run.
"""

def download_dataset(config, start_date, end_date, bbox):
    """Download NASA Earthdata granules for a dataset configuration.

    Args:
        config: ``dotdict`` with at least ``name`` and ``output_folder``. May
            include ``rename_files`` callable applied after download.
        start_date: Inclusive range start (``datetime.date``).
        end_date: Inclusive range end (``datetime.date``).
        bbox: CMR bounding box as ``(west, south, east, north)`` in degrees.

    Side effects:
        Authenticates with ``earthaccess``, downloads granules in parallel, and
        optionally renames files on disk.
    """
    create_folder(config.output_folder)
    
    print(f"Logging in to NASA Earthdata...")
    auth = earthaccess.login()
    
    start_str = start_date.strftime("%Y-%m-%dT00:00:00Z")
    end_str = end_date.strftime("%Y-%m-%dT23:59:59Z")
    
    print(f"Searching for {config.name} from {start_str} to {end_str} inside bbox {bbox}...")
    
    # Search for granules using CMR API
    results = earthaccess.search_data(
        short_name=config.name,
        bounding_box=bbox,
        temporal=(start_str, end_str)
    )
    
    if not results:
        print(f"No granules found for {config.name} in the specified range and area.")
        return
        
    print(f"Found {len(results)} granules. Starting download to {config.output_folder}...")
    
    # Download files (earthaccess downloads in parallel by default)
    downloaded_files = earthaccess.download(results, local_path=config.output_folder)
    
    # Rename files to maintain the short and uniform name format expected by downstream analysis
    if 'rename_files' in config:
        print("Renaming downloaded files...")
        for filepath in downloaded_files:
            file_dir, file_name = os.path.split(filepath)
            try:
                new_name = config.rename_files(file_name)
                new_path = join(file_dir, new_name)
                print(f"Renaming: {file_name} -> {new_name}")
                os.rename(filepath, new_path)
            except Exception as e:
                print(f"Could not rename file {file_name}: {e}")

    print(f"Finished downloading and processing dataset: {config.name}")

# %% Dataset configurations and defaults
def_output_folder = "./test_data/Satellite_Data_Examples/"

# ---------------------- (SST) GHRSST MUR ----------------------
# https://podaac.jpl.nasa.gov/dataset/MUR-JPL-L4-GLOB-v4.1  (analysis, 2002 to present)
sst_ghrsst_v2_mur = dotdict({
    "name": "MUR-JPL-L4-GLOB-v4.1",
    "output_folder": join(def_output_folder, "SST", "GHRSST_MUR"),
    "rename_files": lambda file_name: sst_ghrsst_v2_mur["split_file"](file_name.split("_")[0].split("-")[0]),
    "split_file": lambda date_str: "GHRSST_MUR_" + date_str[:4] + "-" + date_str[4:6] + "-" + date_str[6:8] + ".nc"
})

# ---------------------- (SST) GHRSST CMC ----------------------
# https://podaac.jpl.nasa.gov/dataset/CMC0.1deg-CMC-L4-GLOB-v3.0 (analysis, 2016 to present)
sst_ghrsst_v4_cmc = dotdict({
    "name": "CMC0.1deg-CMC-L4-GLOB-v3.0",
    "output_folder": join(def_output_folder, "SST", "GHRSST_CMC"),
    "rename_files": lambda file_name: sst_ghrsst_v4_cmc["split_file"](file_name.split("_")[0].split("-")[0]),
    "split_file": lambda date_str: "GHRSST_CMC_" + date_str[:4] + "-" + date_str[4:6] + "-" + date_str[6:8] + ".nc"
})

# ---------------------- (SSS) SMAP CAP ----------------------
# https://podaac.jpl.nasa.gov/dataset/SMAP_JPL_L3_SSS_CAP_8DAY-RUNNINGMEAN_V5 (2015 to present)
sss_smap_v5 = dotdict({
    "name": "SMAP_JPL_L3_SSS_CAP_8DAY-RUNNINGMEAN_V5",
    "output_folder": join(def_output_folder, "SSS", "SMAP_8day"),
    "rename_files": lambda file_name: sss_smap_v5["split_file"](file_name.split("_")[3]) if len(file_name.split("_")) > 3 else file_name,
    "split_file": lambda date_str: "SSS_SMAP_v5_" + date_str[:4] + "-" + date_str[4:6] + "-" + date_str[6:8] + ".nc"
})

# Configure search wrappers
def download_by_day(c_date, config, bbox):
    """Download EarthData granules for a single calendar day.

    Args:
        c_date: Target date.
        config: Dataset configuration ``dotdict``.
        bbox: CMR bounding box ``(west, south, east, north)``.
    """
    download_dataset(config, c_date, c_date, bbox)

def download_by_month(year, month, config, bbox):
    """Download EarthData granules for all days in one month.

    Args:
        year: Calendar year.
        month: Calendar month ``1..12``.
        config: Dataset configuration ``dotdict``.
        bbox: CMR bounding box ``(west, south, east, north)``.
    """
    from calendar import monthrange
    start_date = datetime.date(year, month, 1)
    end_date = datetime.date(year, month, monthrange(year, month)[1])
    download_dataset(config, start_date, end_date, bbox)

def download_by_year(year, config, bbox):
    """Download EarthData granules for a full calendar year.

    Args:
        year: Calendar year.
        config: Dataset configuration ``dotdict``.
        bbox: CMR bounding box ``(west, south, east, north)``.
    """
    start_date = datetime.date(year, 1, 1)
    end_date = datetime.date(year, 12, 31)
    download_dataset(config, start_date, end_date, bbox)

# Configure search spatial bounds and temporal bounds
bbox_gom = (-99.0, 17.0, -74.0, 31.0) # Bounding box for Gulf of Mexico

# %%
if __name__ == '__main__':
    start_date = datetime.date(2016, 1, 1)
    end_date = datetime.date(2016, 1, 2)
    
    # Download example dataset (SST GHRSST MUR)
    current_config = sst_ghrsst_v2_mur
    download_dataset(current_config, start_date, end_date, bbox_gom)
