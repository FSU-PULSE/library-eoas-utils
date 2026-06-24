"""Download Copernicus Marine subsets by day, month, or year.

Install::

    mamba install conda-forge::copernicusmarine

Credentials are read from ``~/.netrc`` under the ``COPERNICUS`` machine entry.
"""

# %% 
# INSTALL:
# mamba install conda-forge::copernicusmarine
# copernicusmarine get --help

from calendar import monthrange
import os
import datetime
import netrc

import copernicusmarine as cm

print(f"Version of copernicusmarine: {cm.__version__}")


def _get_copernicus_credentials() -> tuple[str, str]:
    """
    Read Copernicus Marine credentials from ~/.netrc.

    Returns
    -------
    tuple[str, str]
        Username and password for Copernicus Marine API calls.
    """
    secrets = netrc.netrc()
    username, _account, password = secrets.hosts["COPERNICUS"]
    return username, password

def download_by_year(year, cop_ds, bbox, output_folder):
    """Download a full calendar year for one Copernicus dataset.

    Args:
        year: Calendar year.
        cop_ds: Dataset metadata dict from :data:`Copernicus_Datasets`.
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.
        output_folder: Local directory for the NetCDF output.

    Side effects:
        Calls ``copernicusmarine.subset`` with ``force_download=True``.
    """
    username, password = _get_copernicus_credentials()
    start_date = datetime.date(year,1,1)
    end_date = datetime.date(year,12,31)

    if cop_ds['short_name'] != '':
        output_filename = f"{cop_ds['short_name']}_{start_date.year}.nc"
    else:
        output_filename = f"{start_date.year}.nc"

    cm.subset(
        dataset_id=cop_ds['id'],
        dataset_version=cop_ds['version'],
        variables= cop_ds['variables'],
        minimum_longitude=bbox[0],
        maximum_longitude=bbox[2],
        minimum_latitude=bbox[1],
        maximum_latitude=bbox[3],
        start_datetime=start_date.strftime("%Y-%m-%dT00:00:00"),
        end_datetime=end_date.strftime("%Y-%m-%dT00:00:00"),
        output_filename=output_filename,
        output_directory=output_folder,
        username=username,
        password=password,
        force_download=True
    )

def download_by_month(year, cop_ds, bbox, output_folder):
    """Download each month in a calendar year as a separate NetCDF file.

    Args:
        year: Calendar year.
        cop_ds: Dataset metadata dict from :data:`Copernicus_Datasets`.
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.
        output_folder: Local directory for monthly NetCDF files.

    Side effects:
        Prints errors for individual months but continues the loop.
    """
    username, password = _get_copernicus_credentials()
    for month in range(1, 13):
        start_date = datetime.date(year,month,1)
        end_date = datetime.date(year, month, monthrange(year, month)[1])
        if cop_ds['short_name'] != '':
            output_filename = f"{cop_ds['short_name']}_{start_date.year}-{start_date.month:02d}.nc"
        else:
            output_filename = f"{start_date.year}-{start_date.month:02d}.nc"

        try: 
            cm.subset(
                dataset_id=cop_ds['id'],
                dataset_version=cop_ds['version'],
                variables= cop_ds['variables'],
                minimum_longitude=bbox[0],
                maximum_longitude=bbox[2],
                minimum_latitude=bbox[1],
                maximum_latitude=bbox[3],
                start_datetime=start_date.strftime("%Y-%m-%dT00:00:00"),
                end_datetime=end_date.strftime("%Y-%m-%dT00:00:00"),
                output_filename=output_filename,
                output_directory=output_folder,
                username=username,
                password=password,
                force_download=True
            )
        except Exception as e:
            print(f"Error downloading {output_filename}: {e}")

def download_by_day(c_date, cop_ds, bbox, output_folder, output_filename=None):
    """Download a single day for one Copernicus dataset.

    Args:
        c_date: Target ``datetime.date``.
        cop_ds: Dataset metadata dict from :data:`Copernicus_Datasets`.
        bbox: ``(lon_min, lat_min, lon_max, lat_max)`` in degrees.
        output_folder: Local directory for the NetCDF output.
        output_filename: Optional override for the output file name.

    Side effects:
        Prints an error message when the subset call fails.
    """
    username, password = _get_copernicus_credentials()
    if output_filename is None:
        if cop_ds['short_name'] != '':
            output_filename = f"{cop_ds['short_name']}_{c_date.year}-{c_date.month:02d}-{c_date.day:02d}.nc"
        else:
            output_filename = f"{c_date.year}-{c_date.month:02d}-{c_date.day:02d}.nc"

    try:
        cm.subset(
            dataset_id=cop_ds['id'],
            dataset_version=cop_ds['version'],
            variables= cop_ds['variables'],
            minimum_longitude=bbox[0],
            maximum_longitude=bbox[2],
            minimum_latitude=bbox[1],
            maximum_latitude=bbox[3],
            start_datetime=c_date.strftime("%Y-%m-%dT00:00:00"),
            end_datetime=c_date.strftime("%Y-%m-%dT23:59:59"),
            output_filename=output_filename,
            output_directory=output_folder,
            username=username,
            password=password,
            force_download=True
        )
    except Exception as e:
        print(f"Error downloading {output_filename}: {e}")

# %% -------- Download data by year ----------
if __name__ == '__main__':
    from download_data.Copernicus_Datasets import Copernicus_Datasets, Copernicus_Enum

    bbox_gom = (-98.25, 7.25, -55.0, 50.0) # DO NOT DELETE THIS LINE, THIS BBOX ARE IMPORTANT!
    bbox_global = (-180, -90, 180, 90) # DO NOT DELETE THIS LINE, THIS BBOX ARE IMPORTANT!
    
    bbox = bbox_gom
    
    cop_ds = Copernicus_Datasets[Copernicus_Enum.SSH_DUACS_L3_D_SWATHS_2022]
    
    # output_folder = "/unity/f1/ozavala/DATA/GOFFISH/CHLORA/COPERNICUS"
    # output_folder = "/unity/f1/ozavala/DATA/GOFFISH/CHLORA/COPERNICUS_GOM_L3_2016_OLCI_300m"
    # output_folder = "/unity/f1/ozavala/DATA/GOFFISH/AVISO/SSH_L3_SWATHS_GoM_2022/"
    output_folder = "/tmp/OZ/"
    
    for c_year in range(2022, 2025):
        # download_by_year(c_year, cop_ds, bbox, output_folder)
        download_by_month(c_year, cop_ds, bbox, output_folder)

# %% TODO Understand: 
# export COPERNICUSMARINE_DISABLE_SSL_CONTEXT=True
# export COPERNICUSMARINE_MAX_CONCURRENT_REQUESTS=7