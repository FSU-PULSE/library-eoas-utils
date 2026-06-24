"""Batch-generate Loop Current contour pickles from AVISO ADT monthly files."""

#%%
import xarray as xr
from shapely.geometry import LineString
from viz_utils.eoa_viz import EOAImageVisualizer
from viz_utils.constants import PlotMode
from io_utils.io_common import create_folder
import pandas as pd
from os.path import join
from proc_utils.gom import lc_from_ssh
import pickle
# This file generates the LC for the AVISO data for the specified dates
# Output: daily pickle files of (lon, lat) contour pairs via proc_utils.gom.lc_from_ssh

#%% ============ It ge
print("Reading data...")
aviso_folder = "/unity/f1/ozavala/DATA/GOFFISH/AVISO/GoM"
root_output_folder = "/unity/f1/ozavala/DATA/GOFFISH/AVISO/LC"
# Creates a dates array from 1993 to 2022
# dates = pd.date_range(start='1993-01-01', end='2022-01-01', freq='D')
dates = pd.date_range(start='2016-01-01', end='2022-01-01', freq='D')

bbox= (-91, -80, 20, 28)

prev_month = -1
for c_date in dates: 
    try:
        print(c_date)
        c_month = c_date.month
        if c_month != prev_month:
            input_file = join(aviso_folder, f"{c_date.year}-{c_date.month:02d}.nc")
            print(f"Reading file {input_file}")
            adt = xr.open_dataset(input_file, decode_times=False)
            # print(adt.info())

            # Reading specific field and layers
            lons = adt.longitude
            lats = adt.latitude
            prev_month = c_month
            c_year = c_date.year
            output_folder = join(root_output_folder, str(c_year))
            create_folder(output_folder)


        lon = (bbox[0], bbox[1])
        lon_360 = (360 + bbox[0], 360 + bbox[1])
        lat = (bbox[2], bbox[3])
        adt = adt.sel(latitude=slice(lat[0], lat[1]), longitude=slice(lon[0], lon[1]))

        adt_slice = adt.adt[c_date.day-1,:,:]
        lats_adt = adt.latitude
        lons_adt = adt.longitude
        lc = lc_from_ssh(adt_slice.values, lons_adt, lats_adt)

        file_name = join(output_folder, f"{c_date.year}-{c_date.month:02d}-{c_date.day:02d}.pkl")
        # Save as a pickle file
        with open(file_name, 'wb') as f:
            pickle.dump(lc, f)

    except Exception as e:
        print(f"Error processing {c_date}")
        print(e)
        continue