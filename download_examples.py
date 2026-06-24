# %%
"""
Example Script: How to Download Satellite and Model Data with Python
======================================================================
This script provides comprehensive examples demonstrating how to programmatically
download satellite and oceanographic data using the scripts under the `download_data` directory.

Prerequisites:
  1. Set up an environment with required libraries:
     conda install -c conda-forge copernicusmarine earthaccess siphon requests xarray
  2. Setup credentials:
     - NASA EarthData credentials in ~/.netrc (urs.earthdata.nasa.gov) or set environment variables:
       export EARTHDATA_USERNAME="your_username"
       export EARTHDATA_PASSWORD="your_password"
     - COPERNICUS credentials in ~/.netrc (COPERNICUS machine)
     - CICESE credentials in ~/.netrc (CICESE machine)
"""

import os
import sys
import datetime

# Ensure the root directory and download_data are on Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "download_data"))

# %% =====================================================================
# EXAMPLE 1: Downloading from NASA EarthData (using Download_EARTH_DATA)
# =====================================================================
def example_download_nasa_earthdata():
    print("\n--- Example 1: Downloading JPL MUR SST v4.1 using NASA EarthData CMR API ---")
    try:
        from download_data.Download_EARTH_DATA import download_dataset, sst_ghrsst_v2_mur, bbox_gom
        
        # We specify a short time range for the example
        start_date = datetime.date(2019, 5, 5)
        end_date = datetime.date(2019, 5, 5)
        
        print(f"Dataset Config Name: {sst_ghrsst_v2_mur.name}")
        print(f"Output Directory: {sst_ghrsst_v2_mur.output_folder}")
        print(f"Bounding Box (GoM): {bbox_gom}")
        
        print("\nCalling download_dataset...")
        download_dataset(sst_ghrsst_v2_mur, start_date, end_date, bbox_gom)
        print("Success! Check the output directory for downloaded netcdf file(s).")
    except ImportError as e:
        print(f"ImportError: {e}")
        print("Please ensure 'earthaccess' is installed in your python environment (e.g. `pip install earthaccess`).")
    except Exception as e:
        print(f"An error occurred: {e}")

# %% =====================================================================
# EXAMPLE 2: Downloading from Copernicus Marine (using Download_COPERNICUS)
# =====================================================================
def example_download_copernicus():
    print("\n--- Example 2: Downloading SSH DUACS L3 observations from Copernicus ---")
    try:
        import copernicusmarine as cm
        from download_data.Copernicus_Datasets import Copernicus_Datasets, Copernicus_Enum
        from download_data.Download_COPERNICUS import download_by_month
        
        cop_ds = Copernicus_Datasets[Copernicus_Enum.SSH_DUACS_L3_D_SWATHS_2022]
        bbox_gom = (-98.25, 7.25, -55.0, 50.0)
        output_folder = "./test_data/Satellite_Data_Examples/AVISO/SSH_L3_SWATHS_GoM_2022"
        
        print(f"Dataset Name: {cop_ds['name']}")
        print(f"Copernicus ID: {cop_ds['id']}")
        print(f"Output Directory: {output_folder}")
        
        # Download SSH data for January 2022 (this will download month range data)
        print("\nCalling download_by_month for year 2022 (January-December loop or subset)...")
        # To avoid downloading the whole year, we can call cm.subset directly for a single day:
        import netrc
        secrets = netrc.netrc()
        username, _, password = secrets.hosts['COPERNICUS']
        
        start_date = datetime.date(2022, 1, 1)
        end_date = datetime.date(2022, 1, 2)
        output_filename = f"SSH_DUACS_L3_subset_{start_date.strftime('%Y%m%d')}.nc"
        
        os.makedirs(output_folder, exist_ok=True)
        print(f"Downloading subset to {output_filename}...")
        cm.subset(
            dataset_id=cop_ds['id'],
            dataset_version=cop_ds['version'],
            variables=cop_ds['variables'],
            minimum_longitude=bbox_gom[0],
            maximum_longitude=bbox_gom[2],
            minimum_latitude=bbox_gom[1],
            maximum_latitude=bbox_gom[3],
            start_datetime=start_date.strftime("%Y-%m-%dT00:00:00"),
            end_datetime=end_date.strftime("%Y-%m-%dT23:59:59"),
            output_filename=output_filename,
            output_directory=output_folder,
            username=username,
            password=password,
            force_download=True
        )
        print("Success! Copernicus DUACS L3 SSH file downloaded.")
    except KeyError:
        print("Error: No 'COPERNICUS' host entry found in ~/.netrc file.")
        print("Please add Copernicus credentials to ~/.netrc or authenticate first.")
    except ImportError as e:
        print(f"ImportError: {e}")
        print("Please ensure 'copernicusmarine' is installed (e.g. `pip install copernicusmarine`).")
    except Exception as e:
        print(f"An error occurred: {e}")

# %% =====================================================================
# EXAMPLE 3: Downloading SSS from Public RSS Server (using Download_SSS_SMAP_satellite)
# =====================================================================
def example_download_rss_smap():
    print("\n--- Example 3: Downloading SMAP SSS from Remote Sensing Systems (REMSS) ---")
    try:
        from download_data.Download_SSS_SMAP_satellite import parallel_sss_download
        
        output_folder = "./test_data/Satellite_Data_Examples/SSS/SMAP_Global"
        years = [2019]
        
        print(f"Output Directory: {output_folder}")
        print(f"Year: {years[0]}")
        
        # We will download day 125 of 2019 (May 5, 2019)
        # Note: parallel_sss_download downloads all days (1-365) by default.
        # We'll call a modified version or just run for a single day to keep it fast.
        import requests
        from io_utils.io_common import create_folder
        from os.path import join
        
        create_folder(output_folder)
        file_name = "RSS_smap_SSS_L3_8day_running_2019_125_FNL_v05.0.nc"
        URL = f"https://data.remss.com/smap/SSS/V05.0/FINAL/L3/8day_running/2019/{file_name}"
        output_file = join(output_folder, file_name)
        
        print(f"Downloading specific day SMAP file from: {URL}")
        response = requests.get(URL, timeout=30)
        if response.status_code == 200:
            with open(output_file, "wb") as f:
                f.write(response.content)
            print(f"Success! Downloaded SMAP file to {output_file}")
        else:
            print(f"Failed to download SMAP file. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")

# %% =====================================================================
# EXAMPLE 4: Downloading BioRun NEMO Simulation from CICESE (using Download_BioRun_CICESE_Nemo)
# =====================================================================
def example_download_cicese_nemo():
    print("\n--- Example 4: Downloading model run data from CICESE via Thredds Siphon ---")
    try:
        import netrc
        netrc_file = netrc.netrc()
        username, _, password = netrc_file.authenticators("CICESE")
    except Exception:
        print("Error: No 'CICESE' host entry found in ~/.netrc file.")
        print("Credentials for CICESE are required to download NEMO data.")
        return
        
    try:
        from siphon.catalog import TDSCatalog
        
        catalog_url = "https://cigom.cicese.mx/thredds/intercambio/NEMO-GOM36-ERA5_0-S/catalog.html"
        print(f"Accessing catalog: {catalog_url}")
        
        # Print first few datasets available in catalog
        from siphon.http_util import session_manager
        session_manager.set_session_options(auth=(username, password))
        catalog = TDSCatalog(catalog_url)
        print("Available datasets (showing top 5):")
        for i, (dataset_name, dataset) in enumerate(catalog.datasets.items()):
            if i >= 5:
                break
            print(f"  - {dataset_name}")
            
        print("\nRefer to `download_data/Download_BioRun_CICESE_Nemo.py` to see complete automated downloading and daily averaging scripts.")
    except ImportError as e:
        print(f"ImportError: {e}")
        print("Please ensure 'siphon' is installed in your python environment (e.g. `pip install siphon`).")
    except Exception as e:
        print(f"An error occurred: {e}")

# %% =====================================================================
# Main CLI Menu
# =====================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("         EOAS Satellite & Ocean Model Data Download Examples         ")
    print("=" * 70)
    print("Select an option to run a download example:")
    print("  [1] Download NASA EarthData (GHRSST MUR SST via earthaccess)")
    print("  [2] Download Copernicus Marine (SSH DUACS via copernicusmarine)")
    print("  [3] Download RSS SMAP SSS (Salinity from REMSS via requests)")
    print("  [4] Download CICESE NEMO run (Thredds via siphon)")
    print("  [5] Run all examples")
    print("  [q] Quit")
    print("-" * 70)
    
    choice = input("Enter choice: ").strip().lower()
    
    if choice == '1':
        example_download_nasa_earthdata()
    elif choice == '2':
        example_download_copernicus()
    elif choice == '3':
        example_download_rss_smap()
    elif choice == '4':
        example_download_cicese_nemo()
    elif choice == '5':
        example_download_nasa_earthdata()
        example_download_copernicus()
        example_download_rss_smap()
        example_download_cicese_nemo()
    elif choice == 'q':
        print("Exiting.")
    else:
        print("Invalid option selected.")
