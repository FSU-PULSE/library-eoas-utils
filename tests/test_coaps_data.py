# Testing the provided functions
import os
import pytest
from io_utils.coaps_io_data import get_aviso_by_date, get_aviso_by_month, get_sss_by_date, get_sst_ghrsst_by_date, get_chlora_noaa_by_date
from datetime import datetime

c_date = datetime(2016, 1, 10)
c_date_str = c_date.strftime("%Y-%m-%d")
bbox = [17.5, 32.5, -98, -76]

AVISO_DIR = "/unity/f1/ozavala/DATA/GOFFISH/AVISO/GoM/"
SST_DIR = "/unity/f1/ozavala/DATA/GOFFISH/SST/OISST"
SSS_DIR = "/unity/f1/ozavala/DATA/GOFFISH/SSS/SMAP_Global"
CHLORA_DIR = "/unity/f1/ozavala/DATA/GOFFISH/CHLORA/NOAA"

@pytest.mark.skipif(not os.path.exists(AVISO_DIR), reason="AVISO test data folder not found (requires COAPS mount)")
def test_aviso():
    print("Reading monthly aviso data... ")
    aviso_data, lats, lons = get_aviso_by_month(AVISO_DIR, c_date, bbox)
    print(f"The number of times available are: {aviso_data.time.size} for date {c_date_str}")
    assert aviso_data.time.size == 31
    assert lats.size == 60
    assert aviso_data.adt.shape == (31, 60, 88)

    print("Reading daily aviso data... ")
    aviso_data, lats, lons = get_aviso_by_date(AVISO_DIR, c_date, bbox)
    print(f"The number of times available are: {aviso_data.time.size} requested {c_date_str} available {aviso_data.time.values}")
    assert aviso_data.time.size == 1
    assert lats.size == 60
    assert aviso_data.adt.shape == (60, 88)

@pytest.mark.skipif(not os.path.exists(SST_DIR), reason="SST test data folder not found (requires COAPS mount)")
def test_satellite_sst():
    print("Reading SST data... ")
    sst_data, lats, lons = get_sst_ghrsst_by_date(SST_DIR, c_date, bbox)
    assert sst_data.analysed_sst.shape == (1, 1351, 2201)
    assert lats.size == 1351
    assert lons.size == 2201

@pytest.mark.skipif(not os.path.exists(SSS_DIR), reason="SSS test data folder not found (requires COAPS mount)")
def test_satellite_sss():
    c_date = datetime(2016, 1, 10)
    print("Reading SSS data... ")
    sss_data, lats, lons = get_sss_by_date(SSS_DIR, c_date, bbox)
    print(sss_data.sss_smap.shape)
    assert sss_data.sss_smap.shape == (60, 88)
    assert lats.size == 60
    assert lons.size == 88

@pytest.mark.skipif(not os.path.exists(CHLORA_DIR), reason="CHLORA test data folder not found (requires COAPS mount)")
def test_satellite_chlora_noaa():
    c_date = datetime(2019, 1, 10)
    print("Reading chlora data... ")
    chlora_data, lats, lons = get_chlora_noaa_by_date(CHLORA_DIR, c_date, bbox)
    print(chlora_data.variables)
    assert chlora_data.chlor_a.squeeze().shape == (180, 264)
    assert lats.size == 180
    assert lons.size == 264