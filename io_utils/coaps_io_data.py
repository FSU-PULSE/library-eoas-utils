# %% Imports
# Purpose: Functions for reading and writing COAPS data
import os
from os.path import join
from typing import List, Optional, Tuple
import pandas as pd
import xarray as xr
import numpy as np
import cftime
from datetime import date, datetime

# Only if debugging 
import sys
# sys.path.append("../")  # (with interactive window)
sys.path.append("eoas_pyutils")    # (without interactive window)

from io_utils.dates_utils import get_day_of_year_from_month_and_day

# %% AVISO by month
def get_aviso_by_month(aviso_folder: str, c_date: datetime, bbox: Optional[List[float]] = None) -> Tuple[xr.Dataset, xr.DataArray, xr.DataArray]:
    '''
    Reads AVISO monthly data for a given date. You can also specify a bounding box and the data will be cropped to that region.
    '''
    aviso_file_name = join(aviso_folder, f"{c_date.year}-{c_date.month:02d}.nc")
    aviso_data = xr.open_dataset(aviso_file_name)
    if bbox is not None:
        aviso_data = aviso_data.sel(latitude=slice(bbox[0],bbox[1]),
                                    longitude=slice(bbox[2],bbox[3]))

    lats = aviso_data.latitude
    lons = aviso_data.longitude

    return aviso_data, lats, lons

# %% AVISO by date
def get_aviso_by_date(aviso_folder, c_date, bbox=None):
    '''
    Reads AVISO data for a specified date, and optionally crops to a specified bounding box.
    If the standard file naming convention fails, an alternative file naming convention is used.

    Parameters:
        aviso_folder (str): Directory containing AVISO files.
        c_date (datetime.date): Date for which to retrieve data.
        bbox (tuple of float, optional): Bounding box as (min_lat, max_lat, min_lon, max_lon).

    Returns:
        Tuple containing the AVISO dataset, latitudes, and longitudes.
    '''
    # Standard file naming format
    alternative_folder = '/home/jmiranda/Data/SSH/SEALEVEL_GLO_PHY_L4_NRT_008_046/'
    standard_format = join(aviso_folder, f"{c_date.year}-{c_date.month:02d}.nc")
    alternative_format = f"nrt_global_allsat_phy_l4_{c_date.strftime('%Y%m%d')}"
    
    # Attempt to load dataset using standard naming format
    try:
        aviso_data = xr.open_dataset(standard_format)
    except FileNotFoundError:
        # Alternative file naming format when standard file is not found
        files = os.listdir(alternative_folder)
        matching_files = [file for file in files if alternative_format in file]
        
        if not matching_files:
            raise FileNotFoundError(f"No files found for date {c_date} in {alternative_format}")
        
        try:
            aviso_data = xr.open_dataset(join(alternative_folder, matching_files[0]))
        except:
            raise RuntimeError(f"Could not load AVISO data for {c_date}, {matching_files[0]}")

    # Crop to bounding box if specified
    if bbox is not None:
        target_time = np.datetime64(c_date)
        # Calculate the absolute time differences
        time_diff = np.abs(aviso_data["time"] - target_time)
        # Get the index of the closest time
        closest_index = np.argmin(time_diff.values)
        
        # Select data for the closest time and within the specified bounding box
        aviso_data = aviso_data.sel(time=aviso_data["time"][closest_index],
                                    latitude=slice(bbox[0], bbox[1]),
                                    longitude=slice(bbox[2], bbox[3]))

    lats = aviso_data.latitude
    lons = aviso_data.longitude

    return aviso_data, lats, lons

# ========================= SST ======================================
# %% SST GHRSST by date
def get_sst_ghrsst_by_date(sst_folder, c_date, bbox=None):
    '''
    Reads SST single day for a given date. You can also specify a bounding box and the data will be cropped to that region.
    '''
    c_date_str = c_date.strftime("%Y%m%d")
    sst_file_name = join(sst_folder, str(c_date.year), f"{c_date_str}090000-JPL-L4_GHRSST-SSTfnd-MUR-GLOB-v02.0-fv04.1_subset.nc")
    sst_data = xr.open_dataset(sst_file_name)
    if bbox is not None:
        sst_data = sst_data.sel( lat=slice(bbox[0],bbox[1]),
                                lon=slice(bbox[2],bbox[3]))

    lats = sst_data.lat
    lons = sst_data.lon

    return sst_data, lats, lons

# %% SST OSTIA by year
def get_sst_ostia_by_year(sst_folder, year, bbox=None):
    sst_file_name = join(sst_folder, f"OSTIA_SST_{year}.nc")
    sst_data = xr.open_dataset(sst_file_name)
    if bbox is not None:
        sst_data = sst_data.sel(lat=slice(bbox[0], bbox[1]), lon=slice(bbox[2], bbox[3]))

    lats = sst_data.latitude
    lons = sst_data.longitude

    return sst_data, lats, lons


# %% SSS by date
def get_sss_by_date(sss_folder, c_date, bbox=None):
    '''
    Reads salinity single day for a given date. You can also specify a bounding box and the data will be cropped to that region.
    '''
    c_date_str = c_date.strftime("%Y%m%d")

    day_of_year = get_day_of_year_from_month_and_day(c_date.month, c_date.day, year=datetime.now().year)

    sss_file_name = join(sss_folder, str(c_date.year), f"RSS_smap_SSS_L3_8day_running_{c_date.year}_{day_of_year:03d}_FNL_v05.0.nc")
    sss_data = xr.open_dataset(sss_file_name)
    if bbox is not None:
        sss_data = sss_data.sel( lat=slice(bbox[0],bbox[1]),
                                lon=slice((bbox[2] + 360)%360,(bbox[3] + 360)%360))

    lats = sss_data.lat
    lons = np.where(sss_data.lon > 180, sss_data.lon - 360, sss_data.lon)

    return sss_data, lats, lons

# %% Chlora NOAA by date
def get_chlora_noaa_by_date(input_folder, c_date, bbox=None):
    '''
    Reads Chlor-a data single day for a given date. You can also specify a bounding box and the data will be cropped to that region.
    '''
    chlora_file_name = join(input_folder,  f"{c_date.year}-{c_date.month:02d}-{c_date.day:02d}.nc")
    chlora = xr.open_dataset(chlora_file_name)
    if bbox is not None:
        # TODO for some reason the latitude field is flipped
        chlora = chlora.sel( latitude=slice(bbox[1],bbox[0]),
                                       longitude=slice(bbox[2], bbox[3])) 


    lats = chlora.latitude
    lons = chlora.longitude

    return chlora, lats, lons

def get_chlora_noaa_by_date_range(input_folder, start_date, end_date, bbox=None):
    '''
    Reads Chlor-a data for a given date range. You can also specify a bounding box and the data will be cropped to that region.
    '''
    merged_chlora_data = None
    for i, c_date in enumerate(pd.date_range(start=start_date, end=end_date, freq="1D")):
        chlora_file_name = join(input_folder,  f"{c_date.year}-{c_date.month:02d}-{c_date.day:02d}.nc")

        chlora = xr.open_dataset(chlora_file_name)
        if bbox is not None:
            # TODO for some reason the latitude field is flipped
            chlora = chlora.sel( latitude=slice(bbox[1],bbox[0]),
                                        longitude=slice(bbox[2], bbox[3])) 

        if merged_chlora_data is None:
            lats = chlora.latitude
            lons = chlora.longitude
            merged_chlora_data = chlora
        else:
            merged_chlora_data = xr.concat([merged_chlora_data, chlora], dim="time")

    return merged_chlora_data, lats, lons

def get_chlora_copernicus_by_date(input_folder, c_date, bbox=None):
        """
        Retrieves chlorophyll-a data from Copernicus dataset for a specific date.

        Parameters:
        - input_folder (str): The path to the folder containing the Copernicus dataset files.
        - c_date (datetime.datetime): The date for which to retrieve the chlorophyll-a data.
        - bbox (list or None): Optional bounding box coordinates [lat_min, lat_max, lon_min, lon_max]
            to subset the data. Default is None.

        Returns:
        - chlora_c_date (xarray.DataArray): The chlorophyll-a data for the specified date.
        - lats (xarray.DataArray): The latitude values corresponding to the chlorophyll-a data.
        - lons (xarray.DataArray): The longitude values corresponding to the chlorophyll-a data.
        """
        c_year = c_date.year

        cop_files = [x for x in os.listdir(input_folder) if x.find(str(c_year)) != -1]
        assert len(cop_files) == 1, "There should be only one file per year"
        file_name = cop_files[0]
        ds = xr.open_dataset(join(input_folder, file_name))
        chlora = ds.CHL
        c_day_of_year = get_day_of_year_from_month_and_day(c_date.month, c_date.day, c_year)

        chlora_c_date = chlora[c_day_of_year,:,:]

        if bbox is not None:
                chlora_c_date = chlora_c_date.sel(latitude=slice(bbox[0],bbox[1]),
                                                        longitude=slice(bbox[2], bbox[3]))
        
        lats = chlora_c_date.latitude
        lons = chlora_c_date.longitude

        return chlora_c_date, lats, lons

def get_chlora_copernicus_by_date_range(input_folder, start_date, end_date, bbox=None):
    c_start_date = start_date
    c_year = c_start_date.year
    end_year = end_date.year

    merged_chlora_data = None
    while c_start_date < end_date:
        cop_files = [x for x in os.listdir(input_folder) if x.find(str(c_year)) != -1]
        assert len(cop_files) == 1, "There should be only one file per year"
        file_name = cop_files[0]
        ds = xr.open_dataset(join(input_folder, file_name))
        chlora = ds.CHL
        c_day_of_year = get_day_of_year_from_month_and_day(c_start_date.month, c_start_date.day, c_year)
        if end_year == c_year:
            end_day_of_year = get_day_of_year_from_month_and_day(end_date.month, end_date.day, end_year)
            chlora = chlora[c_day_of_year:end_day_of_year]
        else:
            chlora = chlora[c_day_of_year:]

        if bbox is not None:
            chlora = chlora.sel(latitude=slice(bbox[0],bbox[1]),
                                longitude=slice(bbox[2], bbox[3]))

        if merged_chlora_data is None:
            lats = chlora.latitude
            lons = chlora.longitude
            merged_chlora_data = chlora
        else:
            merged_chlora_data = xr.concat([merged_chlora_data, chlora], dim="time")

        c_start_date = date(c_year+1, 1, 1)

    return merged_chlora_data, lats, lons

# %% Get HYCOM GoM data by date
def get_hycom_gom_raw_by_date(c_date, bbox=None):
    '''
    This code obtains the HYCOM GoM runs by date. Depending on the date selected is the run used to access the data. 
    This code only works if executed from the COAPS compute nodes (or if you have the folders mounted in your local machine)
    For 1993 - 2012 we use (50.1) https://www.hycom.org/data/gomu0pt04/expt-50pt1 /nexsan/archive/GOMu0.04_501/data/netcdf
    For 2013 we use (31.0) https://www.hycom.org/data/goml0pt04/expt-31pt0  /nexsan/archive/GOMl0.04_310
    For 2014 - 2018 (32.5) https://www.hycom.org/data/goml0pt04/expt-32pt5  /nexsan/archive/GOMl0.04_325
    For 2019 - Present (90.1m00) https://www.hycom.org/data/goml0pt04/expt-901m000  /nexsan/archive/GOMu0.04_901m000/data/hindcasts

    The names of the fiels are always the same:
    u for zonal velocity
    v for meridional velocity
    w for vertical velocity
    temperature for temperature
    depth for depth
    salinity for salinity
    ssh for surface elevation
    mld for mixed layer depth
    latitude for latitude
    longitude for longitude
    time for time
    '''

    # If the date is between 1993 and 2012
    year = c_date.year
    month = c_date.month
    day = c_date.day
    day_of_year = get_day_of_year_from_month_and_day(month, day, year)
    if  year >= 1993 and year <= 2012:
        print("Using HYCOM GoM 50.1 for years (1993 - 2012)")
        hycom_folder = '/nexsan/archive/GOMu0.04_501/data/netcdf'
        hycom_file_name = join(hycom_folder, str(year), f"hycom_gomu_501_{year}{month:02d}{c_date.day:02d}00_t*.nc")
        hycom_data = xr.open_mfdataset(hycom_file_name, decode_times=False)

        # Rename the variables
        hycom_data = hycom_data.rename({'water_u': 'u', 
                                        'water_v': 'v', 
                                        'water_temp': 'temperature', 
                                        'surf_el': 'ssh',
                                        'lat': 'latitude',
                                        'lon': 'longitude',
                                        })

    elif year == 2013:
        print("Using HYCOM GoM 31.0 for year 2013")
        hycom_folder = '/nexsan/archive/GOMl0.04_310'
        hycom_file_name = join(hycom_folder, str(year), f"hycom_gomu_501_{year}{month:02d}{c_date.day:02d}00_t000.nc")
    elif year >= 2014 and year <= 2018:
        print("Using HYCOM GoM 32.5 for years (2014 - 2018)")
        hycom_folder = '/nexsan/archive/GOMl0.04_325/data'
        day_of_year = get_day_of_year_from_month_and_day(month, c_date.day, year)
        hycom_file_name = join(hycom_folder, str(year), f"archv.{year}_{day_of_year:03d}_*_3z.nc")

        hycom_data = xr.open_mfdataset(hycom_file_name, decode_times=False)
        # Rename the variables
        hycom_data = hycom_data.rename({'MT': 'time',
                                        'Latitude': 'latitude',
                                        'Longitude': 'longitude',
                                        'w_velocity': 'w'
                                        })
    elif year >= 2019:
        print("Using HYCOM GoM 90.1m000 for years (2017 - 2023) hyndcast")
        hycom_folder = '/nexsan/archive/GOMu0.04_901m000/data/hindcasts'
        day_of_year = get_day_of_year_from_month_and_day(month, day, year)
        hycom_file_name = join(hycom_folder, str(year), f"hycom_gomu_901m000_{year}{month:02d}{day:02d}12_t*.nc")

        hycom_data = xr.open_mfdataset(hycom_file_name, decode_times=False)
        # Rename the variables
        hycom_data = hycom_data.rename({'water_u': 'u',
                                        'water_v': 'v',
                                        'water_temp': 'temperature',
                                        'surf_el': 'ssh',
                                        'lat': 'latitude',
                                        'lon': 'longitude',
                                        })


    # hycom_data = xr.open_dataset(hycom_file_name, decode_times=False)

    lats = hycom_data.latitude
    lons = hycom_data.longitude


    if bbox is not None:
        hycom_data = hycom_data.sel(latitude=slice(bbox[0],bbox[1]),
                                    longitude=slice(bbox[2], bbox[3])) 

    return hycom_data, lats, lons

# %% Get CICESE BioRun data by date
def get_biorun_cicese_nemo_by_date(c_date, input_folder="/unity/f1/ozavala/DATA/GOFFISH/CHLORA/CICESE_NEMO_GOM_RAW", bbox=None):
    """
    Retrieves data from the CICESE_NEMO_GOM_RAW dataset based on a given date.

    Parameters:
    - c_date (datetime.date): The date for which the data is requested.
    - bbox (list): A list containing the bounding box coordinates [lat_min, lat_max, lon_min, lon_max]. Default is None.

    Returns:
    - ds (xarray.Dataset): The dataset containing the requested data.
    - lats (xarray.DataArray): The latitude values.
    - lons (xarray.DataArray): The longitude values.
    """

    c_year = c_date.year
    cftime_date = cftime.DatetimeNoLeap(c_date.year, c_date.month, c_date.day)

    # Getting the dimensions of the dataset from random file
    ds = xr.open_dataset(join(input_folder, "GOM36-ERA5_0_1d_20170327_20170724_ptrc_T.nc"))
    lats = ds.nav_lat[:,0]
    lons = ds.nav_lon[0,:]

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
            c_time_idx = np.argmax(times >= np.datetime64(c_date))

            sal_temp_time_idx = np.argmax(ds_sal_temp.time_average_1d.values >= cftime_date)
            ptr_time_idx = np.argmax(ds_ptr.time_average_1d.values >= cftime_date)
            mld_ssh_time_idx = np.argmax(ds_mld_ssh.time_average_1d.values >= cftime_date)

            ds = xr.Dataset( {
                "temperature"    : (("time", "latitude", "longitude"), ds_sal_temp.votemper[sal_temp_time_idx,0,:,:].data[np.newaxis,:,:]),
                "salinity"       : (("time", "latitude", "longitude"), ds_sal_temp.vosaline[sal_temp_time_idx,0,:,:].data[np.newaxis,:,:]),
                "nchl"           : (("time", "latitude", "longitude"), ds_ptr.NCHL[ptr_time_idx,0,:,:].data[np.newaxis,:,:]),
                "dchl"           : (("time", "latitude", "longitude"), ds_ptr.DCHL[ptr_time_idx,0,:,:].data[np.newaxis,:,:]),
                "mld"            : (("time", "latitude", "longitude"), ds_mld_ssh.mld001[mld_ssh_time_idx,:,:].data[np.newaxis,:,:]),
                "ssh"            : (("time", "latitude", "longitude"), ds_mld_ssh.sossheig[mld_ssh_time_idx,:,:].data[np.newaxis,:,:]),
                # "latitude"       : (("lat"), lats.data),
                # "longitude"      : (("lon"), lons.data),
            },
            {"time": [times[c_time_idx]], "latitude": lats.data, "longitude": lons.data})

            ds.attrs = ds_ptr.attrs

            if bbox is not None:
                ds = ds.sel(latitude=slice(bbox[0],bbox[1]),
                                            longitude=slice(bbox[2], bbox[3])) 
            return ds, lats, lons

def get_biorun_cicese_nemo_by_date_range(start_date, end_date, input_folder="/unity/f1/ozavala/DATA/GOFFISH/CHLORA/CICESE_NEMO_GOM_RAW", bbox=None):
    """Get Bio-Run CICESE NEMO data by date range.

    This function retrieves Bio-Run CICESE NEMO data for a specified date range.
    The data can be further filtered by a bounding box if provided.

    Args:
        start_date (str): The start date of the data range in the format 'YYYY-MM-DD'.
        end_date (str): The end date of the data range in the format 'YYYY-MM-DD'.
        bbox (tuple, optional): The bounding box coordinates (lon_min, lat_min, lon_max, lat_max).
            Defaults to None.

    Returns:
        list: A list of Bio-Run CICESE NEMO data for the specified date range and bounding box.
    """
    merged_biorun_data = None

    # Getting the dimensions of the dataset from random file
    ds = xr.open_dataset(join(input_folder, "GOM36-ERA5_0_1d_20170327_20170724_ptrc_T.nc"))
    lats = ds.nav_lat[:,0]
    lons = ds.nav_lon[0,:]

    prev_ptr_file = None
    c_start_date = start_date # This is the date we want to start with

    while c_start_date < end_date:
        cfstart_time_date = cftime.DatetimeNoLeap(c_start_date.year, c_start_date.month, c_start_date.day)
        c_year = c_start_date.year
        # Read all the files that contain "ptrc_T" in the name
        ptr_files = [x for x in os.listdir(input_folder) if x.find("ptrc_T") != -1 and x.find(str(c_year)) != -1]
        # print(f"Files related to {c_year}: {ptr_files}")
        success_to_load = False
        for c_ptr_file in ptr_files:
            # Create a date for the start date of the file. It is the 4th element of the file name and the format is YYYYMMDD
            file_start_date = date(int(c_ptr_file.split("_")[3][0:4]), int(c_ptr_file.split("_")[3][4:6]), int(c_ptr_file.split("_")[3][6:8]))
            file_end_date = date(int(c_ptr_file.split("_")[4][0:4]), int(c_ptr_file.split("_")[4][4:6]), int(c_ptr_file.split("_")[4][6:8]))
            cfend_time_date = cftime.DatetimeNoLeap(end_date.year, end_date.month, end_date.day)
            # print(f"Current date: {c_start_date} File start date: {file_start_date} - File end date: {file_end_date}.")
            # Verify the desired date is withing the range of dates
            if c_start_date >= file_start_date and c_start_date <= file_end_date:
                print(f"Found file {c_ptr_file} Current date: {c_start_date} File start date: {file_start_date} - File end date: {file_end_date}.")
                success_to_load = True
                c_sal_temp_file = c_ptr_file.replace("ptrc_T", "grid_T_SAL_TEMP")
                c_mld_ssh_file = c_ptr_file.replace("ptrc_T", "grid_T_MLD_SSH")

                if c_ptr_file != prev_ptr_file:
                    # print(f"Loading as new file ...")
                    prev_ptr_file = c_ptr_file
                    # PTR file -> DCHL, NCHL
                    # T_SAL_TEMP -> vosaline, votemper
                    # MLD_SSH -> mld001, sossheig
                    ds_ptr = xr.open_dataset(join(input_folder, c_ptr_file))
                    ds_sal_temp = xr.open_dataset(join(input_folder, c_sal_temp_file))
                    ds_mld_ssh = xr.open_dataset(join(input_folder, c_mld_ssh_file))
                # else:
                    # print(f"Skipping as it is the same file ...")

                times = pd.date_range(start=file_start_date, end=file_end_date, freq="1D")

                # Obtain the indexes where the time is greater than the start date and smaller than the end date
                sal_temp_time_idx = np.where(np.logical_and(ds_sal_temp.time_average_1d.values >= cfstart_time_date, ds_sal_temp.time_average_1d.values <= cfend_time_date))[0]
                ptr_time_idx = np.where(np.logical_and(ds_ptr.time_average_1d.values >= cfstart_time_date, ds_ptr.time_average_1d.values <= cfend_time_date))[0]
                mld_ssh_time_idx = np.where(np.logical_and(ds_mld_ssh.time_average_1d.values >= cfstart_time_date, ds_mld_ssh.time_average_1d.values <= cfend_time_date))[0]
                time_idx = sal_temp_time_idx

                # assert len(sal_temp_time_idx) == len(ptr_time_idx) == len(mld_ssh_time_idx), "The number of time indexes is not the same!"
                if not (len(sal_temp_time_idx) == len(ptr_time_idx) == len(mld_ssh_time_idx)):
                    # Choose the one with the smalles lenght and use that as the limit
                    min_len = min(len(sal_temp_time_idx), len(ptr_time_idx), len(mld_ssh_time_idx))
                    sal_temp_time_idx = sal_temp_time_idx[:min_len]
                    ptr_time_idx = ptr_time_idx[:min_len]
                    mld_ssh_time_idx = mld_ssh_time_idx[:min_len]
                    time_idx = time_idx[:min_len]

                ds = xr.Dataset( {
                    "temperature"    : (("time", "latitude", "longitude"), ds_sal_temp.votemper[sal_temp_time_idx,0,:,:].data[np.newaxis,:,:].squeeze()),
                    "salinity"       : (("time", "latitude", "longitude"), ds_sal_temp.vosaline[sal_temp_time_idx,0,:,:].data[np.newaxis,:,:].squeeze()),
                    "nchl"           : (("time", "latitude", "longitude"), ds_ptr.NCHL[ptr_time_idx,0,:,:].data[np.newaxis,:,:].squeeze()),
                    "dchl"           : (("time", "latitude", "longitude"), ds_ptr.DCHL[ptr_time_idx,0,:,:].data[np.newaxis,:,:].squeeze()),
                    "mld"            : (("time", "latitude", "longitude"), ds_mld_ssh.mld001[mld_ssh_time_idx,:,:].data[np.newaxis,:,:].squeeze()),
                    "ssh"            : (("time", "latitude", "longitude"), ds_mld_ssh.sossheig[mld_ssh_time_idx,:,:].data[np.newaxis,:,:].squeeze()),
                    # "latitude"       : (("lat"), lats.data),
                    # "longitude"      : (("lon"), lons.data),
                },
                {"time": times[sal_temp_time_idx], "latitude": lats.data, "longitude": lons.data})

                ds.attrs = ds_ptr.attrs

                if bbox is not None:
                    ds = ds.sel(latitude=slice(bbox[0],bbox[1]),
                                                longitude=slice(bbox[2], bbox[3])) 

                if merged_biorun_data is None:
                    merged_biorun_data = ds
                else:
                    merged_biorun_data = xr.concat([merged_biorun_data, ds], dim="time")

                c_start_date = file_end_date + pd.Timedelta(days=1)
                # print(f"Next date: {c_start_date}")
                break
        if not success_to_load:
            print(f"Warning: No data found for {c_start_date}. Moving to next date.")
            c_start_date = c_start_date + pd.Timedelta(days=1)

    return merged_biorun_data, merged_biorun_data.latitude.values, merged_biorun_data.longitude.values

# %% Main just for testing
if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm

    c_date = date(2019, 1, 10)
    c_date_str = c_date.strftime("%Y-%m-%d")
    bbox = [17.5, 32.5, -98, -76]

    # %% Access CICESE NEMO Run 
    biorun, lats, lons = get_biorun_cicese_nemo_by_date(c_date, bbox)

    # %% TODO move this to a test file
    hycom_data, lats, lons = get_hycom_gom_raw_by_date(c_date, bbox)

    # Make a grid 2x2 with the plots of surf_el, water_temp, salinity and velocity
    fig, axs = plt.subplots(4, 2, figsize=(10, 10))
    # Superior title the date as a string
    fig.suptitle(c_date_str)
    # Plot surf_el
    axs[0, 0].imshow(hycom_data.ssh[0,:,:], origin="lower")
    axs[0, 0].set_title("Surface elevation")
    # Plot water_temp
    axs[0, 1].imshow(hycom_data.temperature[0,0,:,:], origin="lower")
    axs[0, 1].set_title("Water temperature")
    # Plot salinity in log scale
    axs[1, 0].imshow(hycom_data.salinity[0,0,:,:], origin="lower", norm=LogNorm())
    axs[1, 0].set_title("Salinity")
    # Plot velocity
    axs[1, 1].imshow(np.sqrt(hycom_data.u[0,0,:,:]**2 + hycom_data.v[0,0,:,:]**2), origin="lower")
    axs[1, 1].set_title("Velocity")
    # Plot cicese temperature
    axs[2, 0].imshow(biorun.temperature[0,:,:], origin="lower")
    axs[2, 0].set_title("CICESE Temperature")
    # Plot cicese salinity
    axs[2, 1].imshow(biorun.salinity[0,:,:], origin="lower")
    axs[2, 1].set_title("CICESE Salinity")
    # Plot cicese ssh
    axs[3, 0].imshow(biorun.ssh[0,:,:], origin="lower")
    axs[3, 0].set_title("CICESE SSH")
    # Plot cicese nchl
    axs[3, 1].imshow(biorun.nchl[0,:,:], origin="lower")
    axs[3, 1].set_title("CICESE NCHL")

    plt.show()
    print("Done testing!")
