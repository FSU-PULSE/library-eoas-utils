"""NetCDF read helpers and CF standard-name constants for ocean variables."""

from enum import Enum
import os
from os import walk, listdir
from os.path import join

import numpy as np
from netCDF4 import Dataset
import xarray as xr


def read_netcdf_xr(
    file_name: str,
    fields: list,
    replace_to_nan: bool = True,
    rename_fields=[],
) -> dict:
    """Load selected variables from a NetCDF file with xarray.

    Args:
        file_name: Path to the NetCDF file.
        fields: Variable names to extract. An empty list reads all variables.
        replace_to_nan: Reserved for fill-value handling; currently unused but
            kept for API compatibility.
        rename_fields: Optional list of output keys aligned with ``fields``.
            When non-empty, returned dict keys come from ``rename_fields`` rather
            than the original variable names.

    Returns:
        Dictionary mapping variable names (or renamed keys) to
        ``xarray.DataArray`` objects.

    Side effects:
        Prints a warning and drops missing variable names instead of raising.
    """
    nc_file = xr.load_dataset(file_name)
    all_fields = list(nc_file.variables)

    if len(fields) == 0:
        fields = all_fields
    if not (np.all([field in all_fields for field in fields])):
        print(
            F"Warning!!!!! Fields {[field for field in fields if not (field in all_fields)]} are not"
            F" in the netcdf file {file_name}, removing them from the list."
        )
        fields = [field for field in fields if field in all_fields]

    if len(rename_fields) > 0:
        nc_fields = {rename_fields[idx]: nc_file[field] for idx, field in enumerate(fields)}
    else:
        nc_fields = {field: nc_file[field] for field in fields}

    return nc_fields


def read_netcdf(
    file_name: str,
    fields: list,
    replace_to_nan: bool = True,
    rename_fields=[],
) -> dict:
    """Load selected variables from a NetCDF file with netCDF4.

    Args:
        file_name: Path to the NetCDF file.
        fields: Variable names to extract. An empty list reads all variables.
        replace_to_nan: Reserved for fill-value handling; currently unused but
            kept for API compatibility.
        rename_fields: Optional list of output keys aligned with ``fields``.

    Returns:
        Dictionary mapping variable names (or renamed keys) to ``netCDF4.Variable``
        objects from an open dataset handle.

    Side effects:
        Prints a warning and drops missing variable names instead of raising.
        The returned variables reference an open ``Dataset``; callers should
        close the dataset when finished if memory/file handles matter.
    """
    nc_file = Dataset(file_name, "r", format="NETCDF4")
    all_fields = nc_file.variables

    if len(fields) == 0:
        fields = all_fields
    if not (np.all([field in all_fields for field in fields])):
        print(
            F"Warning!!!!! Fields {[field for field in fields if not (field in all_fields)]} are not"
            F" in the netcdf file {file_name}, removing them from the list."
        )
        fields = [field for field in fields if field in all_fields]

    if len(rename_fields) > 0:
        nc_fields = {rename_fields[idx]: all_fields[field] for idx, field in enumerate(fields)}
    else:
        nc_fields = {field: all_fields[field] for field in fields}

    return nc_fields


def xr_summary(ds: xr.Dataset) -> None:
    """Print global attributes, dimensions, coordinates, and variables.

    Args:
        ds: xarray dataset to summarize.

    Side effects:
        Writes formatted summary lines to stdout.
    """
    print("\n========== Global attributes =========")
    for name in ds.attrs:
        print(F"{name} = {getattr(ds, name)}")

    print("\n========== Dimensions =========")
    for name in ds.dims:
        print(F"{name}: {ds[name].shape}")

    print("\n========== Coordinates =========")
    for name in ds.coords:
        print(F"{name}: {ds[name].shape}")

    print("\n========== Variables =========")
    for cur_variable_name in ds.variables:
        cur_var = ds[cur_variable_name]
        print(F"{cur_variable_name}: {cur_var.dims} {cur_var.shape}")


def nc_summary(ds: Dataset) -> None:
    """Print global attributes and variables from a netCDF4 dataset.

    Args:
        ds: Open ``netCDF4.Dataset`` instance.

    Side effects:
        Writes formatted summary lines to stdout.
    """
    print("\n========== Global attributes =========")
    for name in ds.ncattrs():
        print(F"{name} = {getattr(ds, name)}")

    print("\n========== Variables =========")
    netCDFvars = ds.variables
    for cur_variable_name in netCDFvars.keys():
        cur_var = ds.variables[cur_variable_name]
        print(F"Dimensions for {cur_variable_name}: {cur_var.dimensions} {cur_var.shape}")


def read_multiple_netcdf_xarr(file_names: list, fields: list | None = None) -> list:
    """Read the same variable subset from multiple NetCDF files.

    Args:
        file_names: Ordered list of NetCDF file paths.
        fields: Variable names passed to :func:`read_netcdf_xr`. Defaults to
            all variables when empty or ``None``.

    Returns:
        List of per-file dictionaries returned by :func:`read_netcdf_xr`.
    """
    if fields is None:
        fields = []
    datasets = []
    for c_file in file_names:
        datasets.append(read_netcdf_xr(c_file, fields))
    return datasets


class CF_StandardNames(Enum):
    """CF convention standard names for common oceanographic variables.

    Reference:
        http://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html
    """

    TEMP = "sea_water_temperature"
    SALINITY = "sea_water_salinity"
    SSH = "sea_surface_height"
    U = "eastward_sea_water_velocity"
    V = "northward_sea_water_velocity"
    MLD = "sea_water_mixed_layer_thickness"
    CHLORA = "chlorophyll_concentration_in_sea_water"
