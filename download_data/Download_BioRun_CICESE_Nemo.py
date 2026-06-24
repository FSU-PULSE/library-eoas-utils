# %%
from datetime import date, datetime
import netrc
import numpy as np
import pandas as pd
import xarray as xr
import requests
from io import BytesIO
from siphon.catalog import TDSCatalog
from siphon.ncss import NCSS
import requests
from requests.auth import HTTPBasicAuth
from siphon.http_util import session_manager
from os.path import join
import os

# conda install -c conda-forge siphon
# %% 
# This code downloads a bio run from CICESE. The run is for yeas 2016 - 2021


# %% save netcdf file
def save_netcdf_file(url, output_file):
    '''
    Downloads a NetCDF file from a URL and saves it to disk.
    '''
    # Send a GET request to the URL
    print("Downloading data...")
    response = requests.get(url, auth=(username, password))

    # Check if the request was successful (status code 200)
    if response.status_code == 200:
        # Save the data to a file
        with open(output_file, "wb") as file:
            file.write(response.content)
        
        print(f"Data downloaded and saved as '{output_file}'.")
    else:
        print("Failed to download the data. Check your NCSS request URL and try again.")


# %% Download bio run data
def download_biorun_data_raw(output_folder):

    catalog_url = "https://cigom.cicese.mx/thredds/intercambio/NEMO-GOM36-ERA5_0-S/catalog.html"

    netrc_file = netrc.netrc()
    username, _, password = netrc_file.authenticators("CICESE")

    # Access the catalog
    session_manager.set_session_options(auth=(username, password))
    catalog = TDSCatalog(catalog_url)
    for dataset_name, dataset in catalog.datasets.items():
        # Get the download link for the dataset
        # Print the dataset name and download link
        if dataset_name.find("ptrc") != -1 or dataset_name.find("grid_T") != -1:
            print("Dataset:", dataset_name)
            ncss = dataset.subset()
            times = ncss.metadata.time_span

            time_start = times['begin']
            time_end = times['end']

            if dataset_name.find("ptrc") != -1:
                url = f"https://cigom.cicese.mx/thredds/ncss/intercambio/NEMO-GOM36-ERA5_0-S/{dataset_name}?var=DCHL&var=NCHL&disableLLSubset=on&disableProjSubset=on&horizStride=1&time_start={time_start}&time_end={time_end}&timeStride=1&vertCoord=0&addLatLon=true&accept=netcdf"
                output_file = join(output_folder, dataset_name)
                save_netcdf_file(url, output_file)

            if dataset_name.find("grid_T") != -1:
                # "var=mld001&var=sossheig&var=vosaline&var=votemper"
                url = f"https://cigom.cicese.mx/thredds/ncss/intercambio/NEMO-GOM36-ERA5_0-S/{dataset_name}?var=vosaline&var=votemper&disableLLSubset=on&disableProjSubset=on&horizStride=1&time_start={time_start}&time_end={time_end}&timeStride=1&vertCoord=0&addLatLon=true&accept=netcdf"
                output_file = join(output_folder, f"{dataset_name.replace('.nc','')}_SAL_TEMP.nc")
                save_netcdf_file(url, output_file)

                url = f"https://cigom.cicese.mx/thredds/ncss/intercambio/NEMO-GOM36-ERA5_0-S/{dataset_name}?var=mld001&var=sossheig&disableLLSubset=on&disableProjSubset=on&horizStride=1&time_start={time_start}&time_end={time_end}&timeStride=1&vertCoord=0&addLatLon=true&accept=netcdf"
                output_file = join(output_folder, f"{dataset_name.replace('.nc','')}_MLD_SSH.nc")
                save_netcdf_file(url, output_file)


# %% Download the data
# output_folder = "/unity/f1/ozavala/DATA/GOFFISH/CHLORA/CICESE_NEMO_GOM_RAW"
# download_biorun_data_raw(output_folder)

# %% Preprocess data
if __name__ == '__main__':
    input_folder = "/unity/f1/ozavala/DATA/GOFFISH/CHLORA/CICESE_NEMO_GOM_RAW"
    output_folder = "/unity/f1/ozavala/DATA/GOFFISH/CHLORA/CICESE_NEMO_GOM"
    
    c_date = date(2019, 1, 10)
    c_date_str = c_date.strftime("%Y-%m-%d")
    c_year = c_date.year
    
    # Getting the dimensions of the dataset from random file
    ds = xr.open_dataset(join(input_folder, "GOM36-ERA5_0_1d_20170327_20170724_ptrc_T.nc"))
    lats = ds.nav_lat[:,0]
    lons = ds.nav_lon[0,:]
    
    # %%
    # Read all the files that contain "ptrc_T" in the name
    ptr_files = [x for x in os.listdir(input_folder) if x.find("ptrc_T") != -1 and x.find(str(c_year)) != -1]
    # print(ptr_files)
    for c_ptr_file in ptr_files:
        # Create a date for the start date of the file. It is the 4th element of the file name and the format is YYYYMMDD
        c_start_date = date(int(c_ptr_file.split("_")[3][0:4]), int(c_ptr_file.split("_")[3][4:6]), int(c_ptr_file.split("_")[3][6:8]))
        c_end_date = date(int(c_ptr_file.split("_")[4][0:4]), int(c_ptr_file.split("_")[4][4:6]), int(c_ptr_file.split("_")[4][6:8]))
        # Verify the desired date is withing the range of dates
        if c_date >= c_start_date and c_date <= c_end_date:
            print(f"{c_ptr_file}  - Current date: {c_date} - {c_start_date}, {c_end_date}")
            c_sal_temp_file = c_ptr_file.replace("ptrc_T", "grid_T_SAL_TEMP")
            c_mld_ssh_file = c_ptr_file.replace("ptrc_T", "grid_T_MLD_SSH")
            # PTR file -> DCHL, NCHL
            # T_SAL_TEMP -> vosaline, votemper
            # MLD_SSH -> mld001, sossheig
            ds_ptr = xr.open_dataset(join(input_folder, c_ptr_file))
            ds_sal_temp = xr.open_dataset(join(input_folder, c_sal_temp_file))
            ds_mld_ssh = xr.open_dataset(join(input_folder, c_mld_ssh_file))
    
            times = pd.date_range(start=c_start_date, end=c_end_date, freq="1D")
            c_time_idx = np.argmax(times > np.datetime64(c_date))
            ds = xr.Dataset( {
                "temperature"    : (("time", "lat", "lon"), ds_sal_temp.votemper[c_time_idx,0,:,:]),
                "salinity": (("time", "lat", "lon"), ds_sal_temp.vosaline[c_time_idx,0,:,:]),
                "nchl"    : (("time", "lat", "lon"), ds_ptr.NCHL[c_time_idx,0,:,:]),
                "dchl"    : (("time", "lat", "lon"), ds_ptr.DCHL[c_time_idx,0,:,:]),
                "mld"     : (("time", "lat", "lon"), ds_mld_ssh.mld001[c_time_idx,:,:]),
                "ssh"     : (("time", "lat", "lon"), ds_mld_ssh.sossheig[c_time_idx,:,:]),
            },
            {"time": times, "lat": lats, "lon": lons})
            ds.atrs = ds_ptr.atrs