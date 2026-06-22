import os
import sys
import yaml
import datetime
import shutil
from calendar import monthrange
import requests
import xarray as xr
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output, State

# ----------------------------------------------------------------------
# 1. Global Configurations and Paths
# ----------------------------------------------------------------------
CONFIG_FILE = "config.yml"
DEFAULT_DOWNLOAD_DIR = "./test_data/Satellite_Data_Examples"

# Global User-Agent Header to avoid HTTP 403 Forbidden blocks
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_download_folder():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                cfg = yaml.safe_load(f)
                if cfg and "download_folder" in cfg:
                    return cfg["download_folder"]
        except Exception as e:
            print(f"Error reading config.yml: {e}")
    return DEFAULT_DOWNLOAD_DIR

# ----------------------------------------------------------------------
# 2. Variable-Grouped Satellite Products Definition
# ----------------------------------------------------------------------
SATELLITE_PRODUCTS = {
    "sst": {
        "sst_mur_public": {
            "name": "JPL MUR SST v4.1 (Public ERDDAP)",
            "source": "NASA JPL / NOAA ERDDAP (No credentials)",
            "resolution": "0.01° (~1 km original)",
            "period": "2002 - Present",
            "desc": "Daily Foundation Sea Surface Temperature",
            "dir_rel": os.path.join("SST", "OISST"),
            "file_fmt": lambda d: f"{d.year}{d.month:02d}{d.day:02d}090000-JPL-L4_GHRSST-SSTfnd-MUR-GLOB-v02.0-fv04.1_subset.nc",
            "var_name": "analysed_sst",
            "coords": ("lon", "lat"),
            "colorscale": "Thermal",
            "unit": "Temperature (°C)",
            "download_type": "erddap_sst",
            "default_date": "2026-05-05"
        },
        "sst_mur_podaac": {
            "name": "GHRSST MUR JPL L4 (PODAAC)",
            "source": "NASA EarthData PODAAC (Requires netrc credentials)",
            "resolution": "0.01° (~1 km)",
            "period": "2002 - Present",
            "desc": "Multi-scale Ultra-high Resolution SST",
            "dir_rel": os.path.join("SST", "OISST"),
            "file_fmt": lambda d: f"{d.year}{d.month:02d}{d.day:02d}090000-JPL-L4_GHRSST-SSTfnd-MUR-GLOB-v02.0-fv04.1_subset.nc",
            "var_name": "analysed_sst",
            "coords": ("lon", "lat"),
            "colorscale": "Thermal",
            "unit": "Temperature (°C)",
            "download_type": "podaac",
            "default_date": "2026-05-05"
        },
        "sst_cmc_podaac": {
            "name": "GHRSST CMC L4 (PODAAC)",
            "source": "Canada Meteorological Center / PODAAC (Requires netrc)",
            "resolution": "0.1° (~10 km)",
            "period": "2016 - Present",
            "desc": "CMC 0.1 deg Daily SST Analysis",
            "dir_rel": os.path.join("SST", "GHRSST_CMC"),
            "file_fmt": lambda d: f"GHRSST_CMC_{d.year}-{d.month:02d}-{d.day:02d}.nc",
            "var_name": "analysed_sst",
            "coords": ("lon", "lat"),
            "colorscale": "Thermal",
            "unit": "Temperature (°C)",
            "download_type": "podaac",
            "default_date": "2026-05-05"
        },
        "sst_odyssea_nrt": {
            "name": "Copernicus ODYSSEA SST L3 NRT (2021-Present)",
            "source": "Copernicus Marine Service (Requires credentials)",
            "resolution": "0.1° (~10 km)",
            "period": "2021 - Present",
            "desc": "ODYSSEA Global Ocean Sea Surface Temperature Multi-sensor L3 NRT",
            "dir_rel": os.path.join("SST", "ODYSSEA_SST_L3"),
            "file_fmt": lambda d: f"ODYSSEA_SST_L3_NRT_{d.year}-{d.month:02d}.nc",
            "var_name": "sea_surface_temperature",
            "coords": ("longitude", "latitude"),
            "colorscale": "Thermal",
            "unit": "Temperature (°C)",
            "download_type": "copernicus_marine",
            "dataset_id": "IFREMER-GLOB-SST-L3-NRT-OBS_FULL_TIME_SERIE",
            "variables": ["adjusted_sea_surface_temperature", "bias_to_reference_sst", "or_latitude", "or_longitude", "sea_surface_temperature", "sst_dtime"],
            "default_date": "2026-05-05"
        },
        "sst_odyssea_my": {
            "name": "Copernicus ODYSSEA SST L3 MY (1982-2022)",
            "source": "Copernicus Marine Service (Requires credentials)",
            "resolution": "0.1° (~10 km)",
            "period": "1982 - 2022",
            "desc": "Global High Resolution ODYSSEA Sea Surface Temperature Multi-sensor L3 MY",
            "dir_rel": os.path.join("SST", "ODYSSEA_SST_L3"),
            "file_fmt": lambda d: f"ODYSSEA_SST_L3_MY_{d.year}-{d.month:02d}.nc",
            "var_name": "sea_surface_temperature",
            "coords": ("longitude", "latitude"),
            "colorscale": "Thermal",
            "unit": "Temperature (°C)",
            "download_type": "copernicus_marine",
            "dataset_id": "cmems_obs-sst_glo_phy_my_l3s_P1D-m",
            "variables": ["adjusted_sea_surface_temperature", "bias_to_reference_sst", "quality_level", "sea_surface_temperature", "sses_bias", "sses_standard_deviation", "sst_dtime"],
            "default_date": "2019-05-05"
        },
        "sst_ostia_l4": {
            "name": "Copernicus OSTIA SST L4 (2007-Present)",
            "source": "Copernicus Marine Service (Requires credentials)",
            "resolution": "0.05° (~5 km)",
            "period": "2007 - Present",
            "desc": "Global Ocean OSTIA Sea Surface Temperature and Sea Ice Analysis",
            "dir_rel": os.path.join("SST", "OSTIA_SST_L4"),
            "file_fmt": lambda d: f"OSTIA_SST_L4_{d.year}-{d.month:02d}.nc",
            "var_name": "analysed_sst",
            "coords": ("lon", "lat"),
            "colorscale": "Thermal",
            "unit": "Temperature (°C)",
            "download_type": "copernicus_marine",
            "dataset_id": "METOFFICE-GLO-SST-L4-NRT-OBS-SST-V2",
            "variables": ["analysed_sst", "analysis_error", "mask", "sea_ice_fraction"],
            "default_date": "2026-05-05"
        }
    },
    "sss": {
        "sss_smap_public": {
            "name": "RSS SMAP L3 8-day SSS (Public REMSS)",
            "source": "Remote Sensing Systems (No credentials)",
            "resolution": "40 km (~0.25° grid)",
            "period": "2015 - Present",
            "desc": "SMAP 8-day running Sea Surface Salinity",
            "dir_rel": os.path.join("SSS", "SMAP_Global"),
            "file_fmt": lambda d: f"RSS_smap_SSS_L3_8day_running_{d.year}_{d.timetuple().tm_yday:03d}_FNL_v05.0.nc",
            "var_name": "sss_smap_40km",
            "coords": ("lon", "lat"),
            "colorscale": "Haline",
            "unit": "Salinity (psu)",
            "download_type": "remss_sss",
            "default_date": "2026-05-05"
        },
        "sss_smap_jpl": {
            "name": "SMAP JPL L3 SSS CAP 8-Day V5 (PODAAC)",
            "source": "NASA JPL CAP / PODAAC (Requires netrc)",
            "resolution": "60 km (~0.5°)",
            "period": "2015 - Present",
            "desc": "JPL Active-Passive Salinity running mean",
            "dir_rel": os.path.join("SSS", "SMAP_8day"),
            "file_fmt": lambda d: f"SSS_SMAP_v5_{d.year}-{d.month:02d}-{d.day:02d}.nc",
            "var_name": "smap_sss",
            "coords": ("lon", "lat"),
            "colorscale": "Haline",
            "unit": "Salinity (psu)",
            "download_type": "podaac",
            "default_date": "2026-05-05"
        }
    },
    "ssh": {
        "ssh_altimetry_public": {
            "name": "NOAA Altimetry Daily SLA (Public ERDDAP)",
            "source": "NOAA Laboratory for Satellite Altimetry (No credentials)",
            "resolution": "0.25° x 0.25° (~25 km)",
            "period": "2017 - Present",
            "desc": "Sea Surface Height Anomalies from Altimetry",
            "dir_rel": "AVISO",
            "file_fmt": lambda d: f"{d.year}-{d.month:02d}.nc",
            "var_name": "adt",
            "coords": ("longitude", "latitude"),
            "colorscale": "RdBu_r",
            "unit": "ADT / SLA (m)",
            "download_type": "erddap_ssh",
            "default_date": "2026-05-05"
        },
        "ssh_duacs_cmems": {
            "name": "Copernicus DUACS L4 SSH MY (1993-2022)",
            "source": "Copernicus Marine Service (Requires credentials)",
            "resolution": "0.25° x 0.25° (~25 km)",
            "period": "1993 - 2022",
            "desc": "Global Ocean Gridded L4 Sea Surface Heights And Derived Variables Reprocessed 1993",
            "dir_rel": "AVISO",
            "file_fmt": lambda d: f"SSH_DUACS_L4_MY_{d.year}-{d.month:02d}.nc",
            "var_name": "adt",
            "coords": ("longitude", "latitude"),
            "colorscale": "RdBu_r",
            "unit": "Absolute Dynamic Topography (m)",
            "download_type": "copernicus_marine",
            "dataset_id": "cmems_obs-sl_glo_phy-ssh_my_allsat-l4-duacs-0.25deg_P1D",
            "variables": ["adt", "err_sla", "err_ugosa", "err_vgosa", "flag_ice", "sla", "tpa_correction", "ugos", "ugosa", "vgos", "vgosa"],
            "lon_0_360": True,
            "default_date": "2019-05-05"
        },
        "ssh_duacs_nrt": {
            "name": "Copernicus DUACS L4 SSH NRT (2022-Present)",
            "source": "Copernicus Marine Service (Requires credentials)",
            "resolution": "0.25° x 0.25° (~25 km)",
            "period": "2022 - Present",
            "desc": "Global Ocean - Sea Level Anomaly Multi-sensor L4 Observations Since 2022",
            "dir_rel": "AVISO",
            "file_fmt": lambda d: f"SSH_DUACS_L4_NRT_{d.year}-{d.month:02d}.nc",
            "var_name": "adt",
            "coords": ("longitude", "latitude"),
            "colorscale": "RdBu_r",
            "unit": "Absolute Dynamic Topography (m)",
            "download_type": "copernicus_marine",
            "dataset_id": "cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.25deg_P1D",
            "variables": ["adt", "err_sla", "err_ugosa", "err_vgosa", "flag_ice", "sla", "ugos", "ugosa", "vgos", "vgosa"],
            "lon_0_360": True,
            "default_date": "2026-05-05"
        },
        "ssh_duacs_swaths": {
            "name": "Copernicus DUACS L3 SSH Swaths (2022-Present)",
            "source": "Copernicus Marine Service (Requires credentials)",
            "resolution": "Along-track ~7 km",
            "period": "2022 - Present",
            "desc": "Global Ocean Along Track L3 Sea Surface Heights NRT",
            "dir_rel": "AVISO",
            "file_fmt": lambda d: f"SSH_DUACS_L3_SWATHS_{d.year}-{d.month:02d}.nc",
            "var_name": "adt",
            "coords": ("longitude", "latitude"),
            "colorscale": "RdBu_r",
            "unit": "Absolute Dynamic Topography (m)",
            "download_type": "copernicus_marine",
            "dataset_id": "cmems_obs-sl_glo_phy-ssh_nrt_al-l3-duacs_PT1S",
            "variables": ["adt", "sla"],
            "lon_0_360": True,
            "default_date": "2026-05-05"
        }
    },
    "chlora": {
        "chlor_viirs_public": {
            "name": "NOAA Daily VIIRS (Public ERDDAP)",
            "source": "NOAA Coastwatch / ERDDAP (No credentials)",
            "resolution": "9 km (~0.09° grid)",
            "period": "2012 - Present",
            "desc": "VIIRS NPP Daily Chlorophyll-a",
            "dir_rel": os.path.join("CHLORA", "NOAA"),
            "file_fmt": lambda d: f"{d.year}-{d.month:02d}-{d.day:02d}.nc",
            "var_name": "chlor_a",
            "coords": ("longitude", "latitude"),
            "colorscale": "Algae",
            "unit": "Chlorophyll-A (mg/m³)",
            "download_type": "erddap_chlora",
            "default_date": "2026-05-05"
        },
        "chlor_olci_300m": {
            "name": "Copernicus OLCI 300m (CMEMS)",
            "source": "Copernicus Marine / CMEMS (Requires COPERNICUS in netrc)",
            "resolution": "300 m (~0.0027°)",
            "period": "2016 - Present",
            "desc": "OLCI L3 (daily) Bio-Geo-Chemical Observations",
            "dir_rel": os.path.join("CHLORA", "COPERNICUS_300m"),
            "file_fmt": lambda d: f"Ocean_Color_L3_OLCI_300M_{d.year}-{d.month:02d}.nc",
            "var_name": "CHL",
            "coords": ("longitude", "latitude"),
            "colorscale": "Algae",
            "unit": "Chlorophyll-A (mg/m³)",
            "download_type": "copernicus_marine",
            "dataset_id": "cmems_obs-oc_glo_bgc-plankton_my_l3-olci-300m_P1D",
            "variables": ["CHL", "CHL_uncertainty"],
            "default_date": "2026-05-05"
        },
        "chlor_olci_4km": {
            "name": "Copernicus OLCI 4km (CMEMS)",
            "source": "Copernicus Marine / CMEMS (Requires COPERNICUS in netrc)",
            "resolution": "4 km (~0.036°)",
            "period": "2016 - Present",
            "desc": "OLCI L3 (daily) Bio-Geo-Chemical Observations",
            "dir_rel": os.path.join("CHLORA", "COPERNICUS_4km"),
            "file_fmt": lambda d: f"Ocean_Color_L3_OLCI_4km_{d.year}-{d.month:02d}.nc",
            "var_name": "CHL",
            "coords": ("longitude", "latitude"),
            "colorscale": "Algae",
            "unit": "Chlorophyll-A (mg/m³)",
            "download_type": "copernicus_marine",
            "dataset_id": "cmems_obs-oc_glo_bgc-plankton_my_l3-olci-4km_P1D",
            "variables": ["CHL", "CHL_uncertainty"],
            "default_date": "2026-05-05"
        },
        "chlor_l4_gapfree": {
            "name": "Copernicus Gap-Free Chl-A L4 (1997-Present)",
            "source": "Copernicus Marine Service (Requires credentials)",
            "resolution": "4 km (~0.036°)",
            "period": "1997 - Present",
            "desc": "Global Ocean Colour, Bio-Geo-Chemical L4 Gap-free multi-sensor",
            "dir_rel": os.path.join("CHLORA", "COPERNICUS_L4"),
            "file_fmt": lambda d: f"Ocean_Color_L4_GapFree_{d.year}-{d.month:02d}.nc",
            "var_name": "CHL",
            "coords": ("longitude", "latitude"),
            "colorscale": "Algae",
            "unit": "Chlorophyll-A (mg/m³)",
            "download_type": "copernicus_marine",
            "dataset_id": "cmems_obs-oc_glo_bgc-plankton_my_l4-gapfree-multi-4km_P1D",
            "variables": ["CHL", "CHL_uncertainty"],
            "default_date": "2026-05-05"
        }
    }
}

DEFAULT_FALLBACK_DATE = "2019-05-05"

SATELLITE_SUMMARY = {
    "SST": {
        "title": "Sea Surface Temperature (SST)",
        "rows": [
            {
                "satellite": "VIIRS - SNPP, NOAA-20, NOAA-21",
                "instrument": "Visible Infrared Imaging Radiometer Suite",
                "dates": "2012 - present for SNPP; JPSS follow-ons active",
                "l3_resolution": "NOAA ACSPO/CoastWatch L3 daily: 750 m regional/native and 4 km global",
                "l4_resolution": "NOAA Geo-Polar blended L4: 0.05° (~5 km)",
                "source": "NOAA CoastWatch SST products",
                "url": "https://coastwatch.noaa.gov/cwn/product-families/sea-surface-temperature.html",
                "notes": "Infrared SST; cloud-limited, high spatial detail."
            },
            {
                "satellite": "MetOp-A/B/C AVHRR",
                "instrument": "Advanced Very High Resolution Radiometer",
                "dates": "Operational NRT MetOp AVHRR products; heritage record extends back to 1981",
                "l3_resolution": "ACSPO AVHRR L3U: 0.02° gridded uncollated",
                "l4_resolution": "Used by blended and gap-free SST analyses such as OSTIA/MUR",
                "source": "NOAA CoastWatch AVHRR",
                "url": "https://coastwatch.noaa.gov/cwn/instruments/avhrr.html",
                "notes": "Long-running infrared SST backbone for climate and operational products."
            },
            {
                "satellite": "Sentinel-3A/B",
                "instrument": "SLSTR",
                "dates": "2016/2018 - present",
                "l3_resolution": "Inputs support GHRSST/Copernicus L3 and L3S SST products",
                "l4_resolution": "OSTIA L4: 0.05° x 0.05° daily",
                "source": "Copernicus Marine OSTIA",
                "url": "https://data.marine.copernicus.eu/product/SST_GLO_SST_L4_NRT_OBSERVATIONS_010_001/description",
                "notes": "Reference-quality infrared SST input used in operational analyses."
            },
            {
                "satellite": "GCOM-W1 AMSR2 plus GHRSST multi-sensor constellation",
                "instrument": "AMSR2 microwave radiometer, MODIS, AVHRR, VIIRS, in situ inputs",
                "dates": "MUR: 1 Jun 2002 - present",
                "l3_resolution": "Source observations are GHRSST L2P/L3 inputs from several sensors",
                "l4_resolution": "MUR L4: 0.01° (~1 km) daily",
                "source": "NASA PO.DAAC MUR",
                "url": "https://podaac.jpl.nasa.gov/MEaSUREs-MUR",
                "notes": "Gap-free foundation SST analysis used by the dashboard."
            },
            {
                "satellite": "ODYSSEA multi-sensor SST",
                "instrument": "Multi-satellite SST fusion",
                "dates": "NRT: 2021 - present; MY archive: 1982 - 2022",
                "l3_resolution": "ODYSSEA L3S NRT: 0.1° daily; MY L3S: 0.05° daily",
                "l4_resolution": "Not an L4 product",
                "source": "Copernicus Marine ODYSSEA",
                "url": "https://data.marine.copernicus.eu/product/SST_GLO_SST_L3S_NRT_OBSERVATIONS_010_010/description",
                "notes": "Intercalibrated multi-sensor L3S product."
            },
        ],
    },
    "SSS": {
        "title": "Sea Surface Salinity (SSS)",
        "rows": [
            {
                "satellite": "SMAP",
                "instrument": "L-band radiometer at 1.41 GHz",
                "dates": "1 Apr 2015 - present",
                "l3_resolution": "RSS L3 8-day: 40 km experimental and ~70 km standard; JPL CAP L3: 0.25° grid, ~60 km",
                "l4_resolution": "Used in Copernicus multi-observation L4 SSS: 0.125°",
                "source": "NASA PO.DAAC SMAP RSS/JPL",
                "url": "https://podaac.jpl.nasa.gov/dataset/SMAP_RSS_L3_SSS_SMI_8DAY-RUNNINGMEAN_V6",
                "notes": "Primary current satellite salinity source used by the dashboard."
            },
            {
                "satellite": "SMOS",
                "instrument": "MIRAS L-band interferometric radiometer",
                "dates": "12 Jan 2010 - present in Copernicus L3 products",
                "l3_resolution": "Copernicus/NOAA L3: 0.25° x 0.25° daily or 3-day products",
                "l4_resolution": "Used in Copernicus multi-observation L4 SSS: 0.125°",
                "source": "Copernicus Marine SMOS CATDS",
                "url": "https://data.marine.copernicus.eu/product/MULTIOBS_GLO_PHY_SSS_L3_MYNRT_015_014/description",
                "notes": "Complementary current L-band salinity mission."
            },
            {
                "satellite": "SMOS + SMAP + in situ blend",
                "instrument": "Multi-observation optimal interpolation",
                "dates": "1 Jan 1993 - present product timeline; satellite inputs from SMOS/SMAP era",
                "l3_resolution": "Consumes L3 satellite SSS images and in situ salinity",
                "l4_resolution": "Copernicus L4 SSS/SSD: 0.125° x 0.125° daily",
                "source": "Copernicus Marine MultiObs SSS",
                "url": "https://data.marine.copernicus.eu/product/MULTIOBS_GLO_PHY_S_SURFACE_MYNRT_015_013/description",
                "notes": "Gap-free analysis; not currently downloaded by this dashboard."
            },
            {
                "satellite": "Aquarius/SAC-D",
                "instrument": "Aquarius L-band radiometer/scatterometer",
                "dates": "2011 - 2015 mission; historical reference",
                "l3_resolution": "Aquarius L3: 1° mapped SSS",
                "l4_resolution": "No current operational L4 feed",
                "source": "NASA PO.DAAC Aquarius",
                "url": "https://podaac.jpl.nasa.gov/dataset/AQUARIUS_L3_SSS_SMI_CUMULATIVE_V5",
                "notes": "Included for continuity context, not a current instrument."
            },
        ],
    },
    "SSH": {
        "title": "Sea Surface Height (SSH/ADT/SLA)",
        "rows": [
            {
                "satellite": "Sentinel-6 Michael Freilich / Jason-CS",
                "instrument": "Poseidon-4 radar altimeter and microwave radiometer",
                "dates": "2020 - present; Sentinel-6 series extends the reference record toward 2030",
                "l3_resolution": "DUACS along-track L3: 1 Hz (~7 km); some regional 5 Hz (~1 km) sampling",
                "l4_resolution": "DUACS gridded L4: 0.25° x 0.25° daily",
                "source": "EUMETSAT Sentinel-6 / Copernicus",
                "url": "https://www.eumetsat.int/sentinel-6",
                "notes": "Current reference altimetry mission."
            },
            {
                "satellite": "Sentinel-3A/B",
                "instrument": "SRAL radar altimeter",
                "dates": "2016/2018 - present",
                "l3_resolution": "DUACS along-track L3: 1 Hz (~7 km); some regional 5 Hz (~1 km) sampling",
                "l4_resolution": "DUACS gridded L4: 0.25° x 0.25° daily",
                "source": "Copernicus DUACS L3",
                "url": "https://data.marine.copernicus.eu/product/SEALEVEL_GLO_PHY_L3_MY_008_062/description",
                "notes": "Part of the operational multi-mission altimeter constellation."
            },
            {
                "satellite": "Jason-3, SARAL/AltiKa, CryoSat-2, HY-2 series and other nadir altimeters",
                "instrument": "Radar altimeters",
                "dates": "Mission-dependent; available in DUACS multi-mission processing",
                "l3_resolution": "DUACS along-track L3: 1 Hz (~7 km) global sampling",
                "l4_resolution": "DUACS all-satellite L4: 0.25° x 0.25° daily",
                "source": "Copernicus DUACS L4",
                "url": "https://data.marine.copernicus.eu/product/SEALEVEL_GLO_PHY_L4_MY_008_047/description",
                "notes": "Main source family for dashboard Copernicus SSH products."
            },
            {
                "satellite": "SWOT",
                "instrument": "KaRIn wide-swath interferometric altimeter",
                "dates": "16 Dec 2022 - present",
                "l3_resolution": "Research swath products; L2 ocean grid at 2 km x 2 km, native 250 m SSH",
                "l4_resolution": "Not a standard DUACS L4 product in this dashboard",
                "source": "NASA PO.DAAC SWOT",
                "url": "https://podaac.jpl.nasa.gov/dataset/SWOT_L2_LR_SSH_2.0",
                "notes": "High-resolution wide-swath SSH context."
            },
            {
                "satellite": "NOAA RADS multi-altimeter",
                "instrument": "Constellation of radar altimeters",
                "dates": "2017 - present public CoastWatch gridded product",
                "l3_resolution": "NOAA gridded SLA product is described as Level 3 at 0.25°",
                "l4_resolution": "Not labeled as L4 in NOAA CoastWatch",
                "source": "NOAA CoastWatch SSH",
                "url": "https://coastwatch.noaa.gov/cwn/products/sea-level-anomaly-and-geostrophic-currents-multi-mission-global-optimal-interpolation.html",
                "notes": "Public no-credential SSH source used by the dashboard."
            },
        ],
    },
    "Chlorophyll-a": {
        "title": "Chlorophyll-a / Ocean Color (Chl-a)",
        "rows": [
            {
                "satellite": "Sentinel-3A/B",
                "instrument": "OLCI",
                "dates": "2016/2018 - present",
                "l3_resolution": "Copernicus OLCI L3: 300 m and 4 km daily products",
                "l4_resolution": "Copernicus L4 gap-free products: 4 km, with selected finer OLCI-based products",
                "source": "Copernicus Marine Ocean Colour L3/L4",
                "url": "https://data.marine.copernicus.eu/product/OCEANCOLOUR_GLO_BGC_L3_NRT_009_101/description",
                "notes": "Primary high-resolution ocean-color sensor in Copernicus products."
            },
            {
                "satellite": "SNPP and NOAA-20",
                "instrument": "VIIRS",
                "dates": "2012 - present for SNPP; NOAA-20/NPP multi-sensor NRT active",
                "l3_resolution": "NOAA VIIRS ocean color L3 daily composites; 750 m native/regional and 4 km/global products",
                "l4_resolution": "NOAA VIIRS multi-sensor DINEOF gap-filled L4: ~9 km",
                "source": "NOAA CoastWatch VIIRS ocean color",
                "url": "https://coastwatch.noaa.gov/cwn/instruments/viirs.html",
                "notes": "Dashboard public ERDDAP Chl-a source uses VIIRS-derived products."
            },
            {
                "satellite": "PACE",
                "instrument": "OCI hyperspectral ocean color instrument",
                "dates": "Public data release from 11 Apr 2024 - present",
                "l3_resolution": "NASA OCI L3 mapped ocean products: commonly 4 km global; native L2 near 1 km",
                "l4_resolution": "No routine dashboard L4 product",
                "source": "NASA PACE / Earthdata",
                "url": "https://pace.oceansciences.org/access_pace_data.htm",
                "notes": "Newest NASA ocean-color mission; not yet wired into this dashboard."
            },
            {
                "satellite": "GlobColour multi-sensor record",
                "instrument": "Merged ocean-color sensors, including SeaWiFS, MODIS, MERIS/OLCI, VIIRS",
                "dates": "1997 - ongoing",
                "l3_resolution": "Copernicus GlobColour L3 multi-sensor: 4 km daily",
                "l4_resolution": "Copernicus GlobColour L4 gap-free Chl-a: 4 km daily/monthly",
                "source": "Copernicus Marine Ocean Colour L4",
                "url": "https://data.marine.copernicus.eu/product/OCEANCOLOUR_GLO_BGC_L4_MY_009_104/services",
                "notes": "Long-term gap-free Chl-a context for the dashboard L4 product."
            },
        ],
    },
}


def parse_date(date_str):
    return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()


def get_product_date(prod_info):
    return parse_date(prod_info.get("default_date", DEFAULT_FALLBACK_DATE))


def get_product_file_path(prod_info, date_val, root_dir):
    file_name = prod_info["file_fmt"](date_val)
    return os.path.join(root_dir, prod_info["dir_rel"], file_name)


def get_best_local_product_date(prod_info, root_dir):
    return get_product_date(prod_info)


def format_product_date_hint(prod_info):
    return get_product_date(prod_info).strftime("%Y-%m-%d")


# ----------------------------------------------------------------------
# 3. Metadata Layout Generator
# ----------------------------------------------------------------------
def render_metadata_layout(sensor, product_id, stats=None):
    meta = SATELLITE_PRODUCTS[sensor][product_id]
    
    # Left column: Info
    info_rows = [
        html.Div([html.Span("Source: ", className="fw-bold text-muted"), html.Span(meta["source"])]),
        html.Div([html.Span("Resolution: ", className="fw-bold text-muted"), html.Span(meta["resolution"])]),
        html.Div([html.Span("Available: ", className="fw-bold text-muted"), html.Span(meta["period"])]),
        html.Div([html.Span("Description: ", className="fw-bold text-muted small italic"), html.Span(meta["desc"], className="small text-muted")])
    ]
    
    # Right column: Stats
    if stats:
        val_min, val_max, val_mean, shape = stats
        stats_rows = [
            html.Div([html.Span("Min Value: ", className="fw-bold text-muted"), html.Span(f"{val_min:.3f}")]),
            html.Div([html.Span("Max Value: ", className="fw-bold text-muted"), html.Span(f"{val_max:.3f}")]),
            html.Div([html.Span("Mean Value: ", className="fw-bold text-muted"), html.Span(f"{val_mean:.3f}")]),
            html.Div([html.Span("Grid Size: ", className="fw-bold text-muted"), html.Span(f"{shape[0]}x{shape[1]}")])
        ]
    else:
        stats_rows = [
            html.Div("No local file data loaded", className="text-warning small"),
            html.Div("Please download data to view stats", className="text-muted small")
        ]
        
    return dbc.Row([
        dbc.Col(info_rows, md=6, className="border-end border-secondary border-opacity-25"),
        dbc.Col(stats_rows, md=6, className="ps-3")
    ], className="mt-2 pt-2 border-top border-secondary border-opacity-25 small text-muted")


def render_satellite_summary_table(summary):
    header = html.Thead(html.Tr([
        html.Th("Satellite"),
        html.Th("Instrument"),
        html.Th("Dates"),
        html.Th("L3 resolution"),
        html.Th("L4 resolution"),
        html.Th("Source"),
        html.Th("Notes"),
    ]))

    body_rows = []
    for row in summary["rows"]:
        source_link = html.A(
            row["source"],
            href=row["url"],
            target="_blank",
            rel="noopener noreferrer",
            className="summary-source-link",
        )
        body_rows.append(html.Tr([
            html.Td(row["satellite"]),
            html.Td(row["instrument"]),
            html.Td(row["dates"]),
            html.Td(row["l3_resolution"]),
            html.Td(row["l4_resolution"]),
            html.Td(source_link),
            html.Td(row["notes"]),
        ]))

    return dbc.Table(
        [header, html.Tbody(body_rows)],
        bordered=True,
        hover=True,
        responsive=True,
        className="summary-table",
    )


def render_satellite_summary_layout():
    sections = []
    for variable_key, summary in SATELLITE_SUMMARY.items():
        sections.append(
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.H5(summary["title"], className="mb-0 fw-bold text-white"),
                        html.Span(variable_key, className="badge-style badge bg-info text-dark"),
                    ], className="d-flex justify-content-between align-items-center")
                ], className="bg-transparent border-bottom border-secondary py-3"),
                dbc.CardBody([
                    render_satellite_summary_table(summary)
                ], className="p-0")
            ], className="panel-card mb-4")
        )

    return html.Div([
        dbc.Alert([
            html.Strong("Satellite summary metadata. "),
            html.Span("Sources were checked on 2026-06-22; links open the product or mission pages used for the table.")
        ], color="secondary", className="mb-4 panel-card"),
        html.Div(sections)
    ])


def render_satellite_summary_banner():
    return html.Div([
        html.Span("Reference Mode: ", className="text-white"),
        html.Strong("Current Satellite Instruments", className="text-info me-3"),
        html.Span("Variables: ", className="text-white"),
        html.Strong("SST, SSS, SSH, Chl-a", className="text-success")
    ], className="d-flex align-items-center w-100 justify-content-between")

# ----------------------------------------------------------------------
# 4. Downloader Router and Core Functions
# ----------------------------------------------------------------------
def format_file_size(size_bytes):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024 or unit == "TB":
            return f"{size_bytes:.1f} {unit}" if unit != "B" else f"{size_bytes} {unit}"
        size_bytes /= 1024

def get_remote_content_length(url):
    try:
        response = requests.head(url, headers=HEADERS, allow_redirects=True, timeout=20)
        if response.status_code == 200 and response.headers.get("content-length"):
            return int(response.headers["content-length"])
    except Exception:
        return None
    return None

def skip_existing_file(dest_path, label, remote_size=None):
    if not os.path.exists(dest_path):
        return None

    local_size = os.path.getsize(dest_path)
    if local_size <= 0:
        return None

    if remote_size is not None and local_size != remote_size:
        return None

    size_msg = format_file_size(local_size)
    if remote_size is None:
        return True, f"{label} already exists locally ({size_msg}); skipped download: {os.path.basename(dest_path)}"
    return True, f"{label} already downloaded with matching size ({size_msg}); skipped download: {os.path.basename(dest_path)}"

def delete_download_directory_contents(root_dir):
    target = os.path.abspath(os.path.expanduser(root_dir))
    forbidden = {os.path.abspath(os.sep), os.path.abspath(os.path.expanduser("~"))}
    if target in forbidden or len(target) < 6:
        return False, f"Refusing to delete unsafe download target: {target}"
    if not os.path.isdir(target):
        return True, f"Download target does not exist; nothing to delete: {target}"

    removed_items = 0
    removed_bytes = 0
    for entry in os.scandir(target):
        try:
            if entry.is_file() or entry.is_symlink():
                removed_bytes += entry.stat(follow_symlinks=False).st_size
                os.unlink(entry.path)
            elif entry.is_dir():
                for dirpath, _, filenames in os.walk(entry.path):
                    for filename in filenames:
                        path = os.path.join(dirpath, filename)
                        try:
                            removed_bytes += os.path.getsize(path)
                        except OSError:
                            pass
                shutil.rmtree(entry.path)
            removed_items += 1
        except Exception as e:
            return False, f"Failed deleting {entry.path}: {e}"

    os.makedirs(target, exist_ok=True)
    return True, f"Deleted {removed_items} item(s), {format_file_size(removed_bytes)} from: {target}"

def download_via_http(url, dest_path, label):
    try:
        existing = skip_existing_file(dest_path, label, remote_size=get_remote_content_length(url))
        if existing:
            return existing

        response = requests.get(url, headers=HEADERS, timeout=40)
        if response.status_code == 200:
            with open(dest_path, "wb") as f:
                f.write(response.content)
            return True, f"Successfully downloaded {label} data to: {os.path.basename(dest_path)}"
        else:
            return False, f"Failed to download {label} via HTTP. Status code: {response.status_code} ({response.reason})"
    except Exception as e:
        return False, f"HTTP download exception for {label}: {e}"

def download_product(sensor_type, product_id, date_val, root_dir, bbox):
    prod_info = SATELLITE_PRODUCTS[sensor_type][product_id]
    dest_dir = os.path.join(root_dir, prod_info["dir_rel"])
    dest_file = os.path.join(dest_dir, prod_info["file_fmt"](date_val))
    os.makedirs(dest_dir, exist_ok=True)

    existing = skip_existing_file(dest_file, prod_info["name"])
    if existing:
        return existing
    
    dtype = prod_info["download_type"]
    
    if dtype == "erddap_sst":
        date_str = date_val.strftime("%Y-%m-%d")
        url = (f"https://coastwatch.pfeg.noaa.gov/erddap/griddap/jplMURSST41.nc"
               f"?analysed_sst%5B({date_str}T09:00:00Z):1:({date_str}T09:00:00Z)%5D"
               f"%5B({bbox[2]}):1:({bbox[3]})%5D%5B({bbox[0]}):1:({bbox[1]})%5D")
        return download_via_http(url, dest_file, "SST")
        
    elif dtype == "remss_sss":
        year = date_val.year
        day_year = date_val.timetuple().tm_yday
        file_v6 = f"RSS_smap_SSS_L3_8day_running_{year}_{day_year:03d}_FNL_v06.0.nc"
        url = f"https://data.remss.com/smap/SSS/V06.0/FINAL/L3/8day_running/{year}/{file_v6}"
        success, msg = download_via_http(url, dest_file, "SSS")
        if success:
            return True, msg
        url_v5 = f"https://data.remss.com/smap/SSS/V05.0/FINAL/L3/8day_running/{year}/{prod_info['file_fmt'](date_val)}"
        return download_via_http(url_v5, dest_file, "SSS (V5 fallback)")
        
    elif dtype == "erddap_ssh":
        date_str = date_val.strftime("%Y-%m-%d")
        lon_c = [bbox[0] + 360 if bbox[0] < 0 else bbox[0], bbox[1] + 360 if bbox[1] < 0 else bbox[1]]
        url = (f"https://coastwatch.pfeg.noaa.gov/erddap/griddap/nesdisSSH1day_Lon0360.nc"
               f"?sla%5B({date_str}T12:00:00Z):1:({date_str}T12:00:00Z)%5D"
               f"%5B({bbox[2]}):1:({bbox[3]})%5D%5B({lon_c[0]}):1:({lon_c[1]})%5D")
        
        temp_file = dest_file + ".temp"
        success, msg = download_via_http(url, temp_file, "SSH")
        if not success:
            return False, msg
            
        try:
            ds = xr.open_dataset(temp_file)
            rename_dict = {}
            if 'lon' in ds.coords and 'longitude' not in ds.coords:
                rename_dict['lon'] = 'longitude'
            if 'lat' in ds.coords and 'latitude' not in ds.coords:
                rename_dict['lat'] = 'latitude'
            if rename_dict:
                ds = ds.rename(rename_dict)
                
            if 'longitude' in ds.coords:
                ds = ds.assign_coords(longitude=((ds.longitude + 180) % 360) - 180)
                ds = ds.sortby('longitude')
                
            if 'sla' in ds.variables:
                ds = ds.rename({'sla': 'adt'})
                
            ds.to_netcdf(dest_file)
            ds.close()
            os.remove(temp_file)
            return True, f"Successfully processed public SSH (mapped 'sla' to 'adt') and saved to: {os.path.basename(dest_file)}"
        except Exception as e:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            return False, f"Error processing public SSH NetCDF: {e}"
            
    elif dtype == "erddap_chlora":
        date_str = date_val.strftime("%Y-%m-%d")
        url = (f"https://coastwatch.noaa.gov/erddap/griddap/noaacwNPPN20S3ASCIDINEOFDaily.nc"
               f"?chlor_a%5B({date_str}T12:00:00Z):1:({date_str}T12:00:00Z)%5D%5B(0.0):1:(0.0)%5D"
               f"%5B({bbox[3]}):1:({bbox[2]})%5D%5B({bbox[0]}):1:({bbox[1]})%5D")
        return download_via_http(url, dest_file, "Chlorophyll-A")
        
    elif dtype == "podaac":
        import earthaccess
        try:
            # Login (reads credentials from environment or .netrc, prompts if needed)
            earthaccess.login()
            
            shortname = "MUR-JPL-L4-GLOB-v4.1" if "sst_mur" in product_id else ("CMC0.1deg-CMC-L4-GLOB-v3.0" if "sst_cmc" in product_id else "SMAP_JPL_L3_SSS_CAP_8DAY-RUNNINGMEAN_V5")
            start_t = date_val.strftime("%Y-%m-%dT00:00:00Z")
            end_t = date_val.strftime("%Y-%m-%dT23:59:59Z")
            
            # Search for granule
            results = earthaccess.search_data(
                short_name=shortname,
                bounding_box=(bbox[0], bbox[2], bbox[1], bbox[3]),
                temporal=(start_t, end_t)
            )
            if not results:
                return False, f"No granules found for PODAAC product {shortname} on this date."
                
            # Download file
            downloaded = earthaccess.download(results, local_path=dest_dir, force=False)
            if not downloaded:
                return False, f"Failed to download PODAAC product {shortname}."
                
            # Rename the downloaded file to the expected local filename
            expected_name = prod_info["file_fmt"](date_val)
            expected_path = os.path.join(dest_dir, expected_name)
            if os.path.exists(downloaded[0]) and downloaded[0] != expected_path:
                if os.path.exists(expected_path):
                    os.remove(expected_path)
                os.rename(downloaded[0], expected_path)
                
            return True, f"Successfully downloaded and processed PODAAC product {shortname} using earthaccess."
        except Exception as e:
            return False, f"earthaccess download failed: {e}"
            
    elif dtype == "copernicus_marine" or dtype == "motu_ssh":
        has_cm = shutil.which("copernicusmarine") is not None or "copernicusmarine" in sys.modules
        if not has_cm:
            return False, "Error: 'copernicusmarine' library not installed. Install with: pip install copernicusmarine"
        import netrc
        try:
            secrets = netrc.netrc()
            username, account, password = secrets.hosts['COPERNICUS']
        except Exception:
            return False, "Error: No credentials found for host 'COPERNICUS' in ~/.netrc."
            
        try:
            import copernicusmarine as cm_lib
            dataset_id = prod_info.get("dataset_id")
            variables = prod_info.get("variables", ["CHL"])
            
            # Shift longitude to 0-360 range if the dataset expects it
            min_lon = bbox[0]
            max_lon = bbox[1]
            if prod_info.get("lon_0_360", False):
                min_lon = bbox[0] + 360 if bbox[0] < 0 else bbox[0]
                max_lon = bbox[1] + 360 if bbox[1] < 0 else bbox[1]
                
            cm_lib.subset(
                dataset_id=dataset_id,
                dataset_version=prod_info.get("version"),
                variables=variables,
                minimum_longitude=min_lon,
                maximum_longitude=max_lon,
                minimum_latitude=bbox[2],
                maximum_latitude=bbox[3],
                start_datetime=date_val.strftime("%Y-%m-%dT00:00:00"),
                end_datetime=date_val.strftime("%Y-%m-%dT23:59:59"),
                output_filename=prod_info["file_fmt"](date_val),
                output_directory=dest_dir,
                username=username,
                password=password,
                overwrite=False,
                skip_existing=True,
            )
            return True, f"Successfully downloaded Copernicus Marine product: {prod_info['name']}"
        except Exception as e:
            return False, f"Copernicus Marine download exception: {e}"
            
    return False, f"Unknown download type: {dtype}"

# ----------------------------------------------------------------------
# 5. Data Slicing and Coordinate Standardizations
# ----------------------------------------------------------------------
def standardize_coords(ds, lon_var='longitude', lat_var='latitude'):
    rename_dict = {}
    for c in ds.coords:
        if c.lower() in ['lon', 'longitude', 'lons'] and c != lon_var:
            rename_dict[c] = lon_var
        if c.lower() in ['lat', 'latitude', 'lats'] and c != lat_var:
            rename_dict[c] = lat_var
    if rename_dict:
        ds = ds.rename(rename_dict)
    
    # Map [0, 360] -> [-180, 180]
    lons = ds[lon_var].values
    if np.max(lons) > 180:
        ds = ds.assign_coords({lon_var: ((ds[lon_var] + 180) % 360) - 180})
        ds = ds.sortby(lon_var)
    return ds

def load_dataset_slice(sensor_type, product_id, date_val, root_dir, bbox, stride=1):
    prod_info = SATELLITE_PRODUCTS[sensor_type][product_id]
    file_name = prod_info["file_fmt"](date_val)
    file_path = os.path.join(root_dir, prod_info["dir_rel"], file_name)
    
    if not os.path.exists(file_path):
        return None, "File not downloaded"
        
    try:
        ds = xr.open_dataset(file_path)
        
        lon_var, lat_var = prod_info["coords"]
        ds = standardize_coords(ds, lon_var, lat_var)
        
        # Crop bounds
        if ds[lat_var].values[0] > ds[lat_var].values[-1]:
            ds_subset = ds.sel({lat_var: slice(bbox[3], bbox[2]), lon_var: slice(bbox[0], bbox[1])})
        else:
            ds_subset = ds.sel({lat_var: slice(bbox[2], bbox[3]), lon_var: slice(bbox[0], bbox[1])})
            
        var_name = prod_info["var_name"]
        if var_name not in ds_subset.variables:
            visualizable_vars = [v for v in ds_subset.variables if len(ds_subset[v].shape) >= 2]
            if visualizable_vars:
                var_name = visualizable_vars[0]
            else:
                ds.close()
                return None, f"Variable '{var_name}' not found in NetCDF file"
                
        data_var = ds_subset[var_name]
        
        # Force 2D slice
        while len(data_var.shape) > 2:
            data_var = data_var[0]
            
        lons = ds_subset[lon_var].values
        lats = ds_subset[lat_var].values
        values = data_var.values
        ds.close()
        
        # Specific Kelvin conversion for SST
        if sensor_type == "sst" and np.nanmax(values) > 200:
            values = values - 273.15
            
        # Specific log10 conversion for Chlorophyll-A
        unit_label = prod_info["unit"]
        if sensor_type == "chlora":
            # Mask values <= 0 to NaN to avoid log10 errors on negative/zero values
            values = np.where(values > 0, np.log10(values), np.nan)
            unit_label = "log10(Chlorophyll-A) (mg/m³)"
            
        lc_coords = None
        if sensor_type == "ssh" and var_name == "adt":
            try:
                from proc_utils.gom import lc_from_ssh
                lc = lc_from_ssh(values, lons, lats)
                if lc is not None:
                    lc_coords = list(lc)
            except Exception as e:
                print(f"Error extracting Loop Current: {e}")
                
        # Apply subsampling stride for visualization performance
        if stride > 1:
            values = values[::stride, ::stride]
            lons = lons[::stride]
            lats = lats[::stride]
                
        if sensor_type == "ssh":
            return (lons, lats, values, prod_info["colorscale"], unit_label, lc_coords), None
        else:
            return (lons, lats, values, prod_info["colorscale"], unit_label), None
            
    except Exception as e:
        return None, f"Error reading NetCDF file: {e}"

# ----------------------------------------------------------------------
# 6. Dash UI Layout (Modern Dark theme)
# ----------------------------------------------------------------------
PLOTLY_GRAPH_CONFIG = {
    "displayModeBar": True,
    "scrollZoom": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "zoomIn2d", "zoomOut2d"],
}

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    title="EOAS Satellite Data Dashboard"
)

# Custom premium styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                background: linear-gradient(135deg, #090d16 0%, #111827 100%);
                background-attachment: fixed;
                font-family: 'Outfit', 'Inter', system-ui, -apple-system, sans-serif;
                color: #f8fafc;
            }
            .sidebar-card {
                background: rgba(17, 24, 39, 0.7);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 16px;
            }
            .panel-card {
                background: rgba(31, 41, 55, 0.6);
                backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 16px;
                transition: all 0.3s ease;
            }
            .panel-card:hover {
                border-color: rgba(99, 102, 241, 0.3);
                box-shadow: 0 12px 20px -10px rgba(99, 102, 241, 0.2);
            }
            .glow-btn {
                background: linear-gradient(90deg, #6366f1 0%, #06b6d4 100%);
                border: none;
                border-radius: 8px;
                font-weight: 600;
                transition: all 0.3s ease;
            }
            .glow-btn:hover {
                transform: scale(1.02);
                box-shadow: 0 0 15px rgba(99, 102, 241, 0.5);
            }
            .badge-style {
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 0.75rem;
                font-weight: 600;
            }
            .console-footer {
                margin-top: 0.5rem;
            }
            .console-output {
                background: #030712;
                border: 1px solid #1f2937;
                border-radius: 8px;
                font-family: 'Fira Code', monospace;
                font-size: 0.8rem;
                padding: 12px;
                min-height: 120px;
                height: 200px;
                max-height: 50vh;
                resize: vertical;
                overflow: auto;
                color: #38bdf8;
                width: 100%;
                margin-bottom: 0;
                white-space: pre-wrap;
                word-break: break-word;
            }
            .nav-pills .nav-link {
                background: rgba(31, 41, 55, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.05);
                color: #9ca3af;
                margin-right: 8px;
                border-radius: 8px;
                transition: all 0.2s ease;
            }
            .nav-pills .nav-link.active {
                background: linear-gradient(90deg, #6366f1 0%, #4f46e5 100%);
                color: white;
                box-shadow: 0 4px 10px rgba(99, 102, 241, 0.3);
            }
            .loading-status {
                min-height: 1.5rem;
            }
            .summary-table {
                color: #e5e7eb;
                font-size: 0.84rem;
                margin-bottom: 0;
            }
            .summary-table th {
                color: #a5b4fc;
                background: rgba(15, 23, 42, 0.9);
                border-color: rgba(148, 163, 184, 0.22);
                white-space: nowrap;
            }
            .summary-table td {
                background: rgba(15, 23, 42, 0.35);
                border-color: rgba(148, 163, 184, 0.18);
                vertical-align: top;
            }
            .summary-source-link {
                color: #67e8f9;
                text-decoration: none;
                font-weight: 600;
            }
            .summary-source-link:hover {
                color: #a5f3fc;
                text-decoration: underline;
            }
            ._dash-loading {
                margin: 0 auto;
            }
            ._dash-loading-callback {
                font-family: 'Outfit', 'Inter', system-ui, -apple-system, sans-serif;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

app.layout = dbc.Container([
    # Header Row
    dbc.Row([
        dbc.Col([
            html.Div([
                html.H1("EOAS Satellite Data Dashboard", className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400 fw-bold mb-0 mt-3", style={"backgroundImage": "linear-gradient(to right, #818cf8, #22d3ee)", "-webkit-background-clip": "text", "-webkit-text-fill-color": "transparent"}),
                html.P("Gulf of Mexico Variable-Grouped Satellite Remote Sensing Portal", className="text-muted small mb-3")
            ], className="border-bottom border-secondary mb-3 pb-2")
        ])
    ]),
    
    # Tabs Row (stretches full width, high up in the page)
    dbc.Row([
        dbc.Col([
            dbc.Tabs([
                dbc.Tab(label="Sea Surface Temperature (SST)", tab_id="sst"),
                dbc.Tab(label="Sea Surface Salinity (SSS)", tab_id="sss"),
                dbc.Tab(label="Sea Surface Height (SSH/ADT)", tab_id="ssh"),
                dbc.Tab(label="Chlorophyll-A", tab_id="chlora"),
                dbc.Tab(label=". Satellite summary", tab_id="satellite-summary"),
            ], id="variable-tabs", active_tab="sst", className="nav-pills mb-4")
        ], width=12)
    ]),
    
    # Main Content Row (Sidebar on left, Panels container on right)
    dbc.Row([
        # Sidebar Controls
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Dashboard Controls", className="card-title text-indigo-300 fw-bold border-bottom pb-2 mb-3", style={"color": "#a5b4fc"}),
                    
                    # Target Folder Info
                    html.Label("Download Target Directory", className="fw-bold small text-muted"),
                    html.Div(get_download_folder(), className="small bg-dark text-info p-2 rounded mb-3 border border-secondary", style={"wordBreak": "break-all"}),
                    

                    
                    # Subsample Stride Selector
                    html.Label("Subsample Ratio (Visualization)", className="fw-bold small text-muted"),
                    html.Div([
                        dcc.Dropdown(
                            id="subsample-stride",
                            options=[
                                {"label": "1/1 (Full Resolution)", "value": 1},
                                {"label": "1/2 Subsample", "value": 2},
                                {"label": "1/4 Subsample (Default)", "value": 4},
                                {"label": "1/8 Subsample", "value": 8},
                                {"label": "1/16 Subsample", "value": 16},
                            ],
                            value=4,
                            clearable=False,
                            className="text-dark mb-3"
                        )
                    ]),
                    
                    # Hover Toggle Selector
                    html.Label("Tooltip Options", className="fw-bold small text-muted"),
                    dbc.Checklist(
                        options=[
                            {"label": "Enable Hover Tooltips", "value": "hover"}
                        ],
                        value=["hover"],
                        id="hover-toggle",
                        switch=True,
                        className="small mb-3 text-white"
                    ),
                    html.Label("Region of Interest (GoM Bounds)", className="fw-bold small text-muted"),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Lon Min", className="small text-muted mb-0"),
                            dcc.Input(id="lon-min", type="number", value=-98.0, className="form-control form-control-sm bg-dark text-white border-secondary")
                        ], width=6),
                        dbc.Col([
                            html.Label("Lon Max", className="small text-muted mb-0"),
                            dcc.Input(id="lon-max", type="number", value=-60.0, className="form-control form-control-sm bg-dark text-white border-secondary")
                        ], width=6)
                    ], className="mb-2"),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Lat Min", className="small text-muted mb-0"),
                            dcc.Input(id="lat-min", type="number", value=7.5, className="form-control form-control-sm bg-dark text-white border-secondary")
                        ], width=6),
                        dbc.Col([
                            html.Label("Lat Max", className="small text-muted mb-0"),
                            dcc.Input(id="lat-max", type="number", value=50.0, className="form-control form-control-sm bg-dark text-white border-secondary")
                        ], width=6)
                    ], className="mb-3"),
                    
                    # Dynamic Checklist label and checklist
                    html.Label("Select Satellite / Products", className="fw-bold small text-muted mb-2", id="checklist-label", style={"color": "#a5b4fc"}),
                    dbc.Checklist(
                        options=[],
                        value=[],
                        id="product-checklist",
                        className="small mb-4 text-white"
                    ),
                    
                    # Download Button
                    dbc.Button(
                        "Download Selected",
                        id="btn-download",
                        className="w-100 glow-btn mb-2 py-2 text-white"
                    ),
                    dcc.ConfirmDialogProvider(
                        children=dbc.Button(
                            "Delete Data",
                            id="btn-delete-data",
                            color="danger",
                            outline=True,
                            className="w-100 mb-2 py-2"
                        ),
                        id="confirm-delete-data",
                        message=f"Delete all files and folders inside {get_download_folder()}?"
                    ),
                    html.Div(id="download-loading-status", className="loading-status text-center small mb-3"),
                ])
            ], className="sidebar-card mb-4")
        ], md=4, lg=3),
        
        # Dynamic Panels Container
        dbc.Col([
            dcc.Loading(
                id="loading-main",
                type="circle",
                color="#6366f1",
                children=html.Div([
                    dbc.Alert(
                        id="status-banner",
                        color="info",
                        className="mb-4 d-flex justify-content-between align-items-center py-2 px-3 panel-card",
                        style={"border": "1px solid rgba(255, 255, 255, 0.05)"},
                    ),
                    html.Div(id="main-panels-container"),
                ]),
            ),
        ], md=8, lg=9)
    ]),

    # Activity Log Footer (full width)
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Label("Activity Log Console", className="fw-bold small text-muted mb-2"),
                    html.Pre(id="console-log", className="console-output", children="System initialized. Ready for operations.")
                ], className="py-3")
            ], className="sidebar-card console-footer mb-4")
        ], width=12)
    ])
], fluid=True, className="px-4 py-2")

# ----------------------------------------------------------------------
# 7. Callback logic
# ----------------------------------------------------------------------

# Callback 1: Dynamically update product checklist options and values depending on active tab
@app.callback(
    [
        Output("product-checklist", "options"),
        Output("product-checklist", "value"),
        Output("checklist-label", "children")
    ],
    [Input("variable-tabs", "active_tab")]
)
def update_checklist_options(active_tab):
    if active_tab == "satellite-summary":
        return [], [], "Satellite summary"

    options = []
    for key, info in SATELLITE_PRODUCTS[active_tab].items():
        res_str = info["resolution"].split("(")[0].strip()
        label_text = f"{info['name']} ({res_str}) (Date: {format_product_date_hint(info)})"
        options.append({"label": label_text, "value": key})
    # By default, select all available options
    value = [key for key in SATELLITE_PRODUCTS[active_tab].keys()]
    
    label_mapping = {
        "sst": "Select SST Satellites",
        "sss": "Select SSS Satellites",
        "ssh": "Select SSH Products",
        "chlora": "Select Chlorophyll Satellites",
        "satellite-summary": "Satellite summary",
    }
    label = label_mapping.get(active_tab, "Select Satellite / Products")
    
    return options, value, label

_DOWNLOAD_LOADING_INDICATOR = html.Div(
    "Processing data, please wait...",
    className="text-info text-center",
)

_STATUS_BANNER_LOADING = html.Div(
    "Processing satellite data...",
    className="text-white",
)


# Callback 2: Execute downloads and render selected products in a dynamic grid
@app.callback(
    [
        Output("console-log", "children"),
        Output("status-banner", "children"),
        Output("main-panels-container", "children"),
    ],
    [
        Input("btn-download", "n_clicks"),
        Input("confirm-delete-data", "submit_n_clicks"),
        Input("product-checklist", "value"),
        Input("subsample-stride", "value"),
        Input("hover-toggle", "value"),
    ],
    [
        State("variable-tabs", "active_tab"),
        State("lon-min", "value"),
        State("lon-max", "value"),
        State("lat-min", "value"),
        State("lat-max", "value"),
        State("console-log", "children"),
    ],
    running=[
        (Output("btn-download", "disabled"), True, False),
        (Output("btn-delete-data", "disabled"), True, False),
        (Output("download-loading-status", "children"), _DOWNLOAD_LOADING_INDICATOR, ""),
        (Output("status-banner", "children"), _STATUS_BANNER_LOADING, ""),
    ],
    prevent_initial_call=False,
)
def handle_operations(n_clicks, delete_n_clicks, selected_prods, stride, hover_toggle, active_tab, lon_min, lon_max, lat_min, lat_max, existing_log):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None
    
    try:
        stride_val = int(stride)
    except (ValueError, TypeError):
        stride_val = 4
        
    root_dir = get_download_folder()
    bbox = (lon_min, lon_max, lat_min, lat_max)
    
    log_messages = []

    if active_tab == "satellite-summary":
        if triggered_id == "btn-download":
            log_messages.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Satellite summary tab selected; no data download is needed.")
        elif triggered_id == "confirm-delete-data" and delete_n_clicks:
            success, msg = delete_download_directory_contents(root_dir)
            status = "Deleted data" if success else "Delete failed"
            log_messages.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {status}: {msg}")
        else:
            log_messages.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Active Tab: Satellite Summary | Showing current instrument reference tables")

        full_log = "\n".join(log_messages) + "\n\n" + (existing_log if existing_log else "")
        full_log = full_log[:5000]
        return full_log, render_satellite_summary_banner(), render_satellite_summary_layout()
    
    # --------------------------------------------------
    # Triggered by click: Execute downloads for ALL checked products
    # --------------------------------------------------
    if triggered_id == "confirm-delete-data" and delete_n_clicks:
        success, msg = delete_download_directory_contents(root_dir)
        status = "Deleted data" if success else "Delete failed"
        log_messages.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] {status}: {msg}")
    elif triggered_id == "btn-download" and n_clicks and selected_prods:
        log_messages.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Starting batch download of {len(selected_prods)} selected product(s)...")
        for prod_id in selected_prods:
            prod_info = SATELLITE_PRODUCTS[active_tab][prod_id]
            prod_name = prod_info["name"]
            date_val = get_product_date(prod_info)
            date_str = date_val.strftime("%Y-%m-%d")
            log_messages.append(f"Downloading product: {prod_name} for date: {date_str}...")
            success, msg = download_product(active_tab, prod_id, date_val, root_dir, bbox)
            log_messages.append(msg)
        log_messages.append("Finished all download operations.")
    else:
        log_messages.append(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Active Tab: {active_tab.upper()} | Visualizing Dataset Dates")
        
    full_log = "\n".join(log_messages) + "\n\n" + (existing_log if existing_log else "")
    full_log = full_log[:5000] # Cap log display size
    
    # Return placeholder layout if no product is selected
    if not selected_prods:
        banner_content = html.Div([
            html.Span("Visualization Mode: ", className="text-white"),
            html.Strong("Dataset Dates", className="text-info me-3"),
            html.Span("No products selected", className="text-warning")
        ], className="d-flex align-items-center w-100 justify-content-between")
        
        placeholder_layout = dbc.Card([
            dbc.CardBody([
                html.H4("No Products Selected", className="text-warning text-center fw-bold mb-2"),
                html.P("Please check one or more satellite products in the sidebar to visualize and analyze data.", className="text-muted text-center small mb-0")
            ], className="py-5")
        ], className="panel-card")
        
        return full_log, banner_content, placeholder_layout
        
    # --------------------------------------------------
    # Load and Render Files for checked products in dynamic grid
    # --------------------------------------------------
    panel_cards = []
    found_count = 0
    
    # Determine columns layout
    num_selected = len(selected_prods)
    if num_selected == 1:
        col_width = 12
    elif num_selected == 2:
        col_width = 6
    else:
        col_width = 4
        
    for prod_id in selected_prods:
        prod_info = SATELLITE_PRODUCTS[active_tab][prod_id]
        date_val = get_best_local_product_date(prod_info, root_dir)
        date_str = date_val.strftime("%Y-%m-%d")
        file_path = get_product_file_path(prod_info, date_val, root_dir)
        exists = os.path.exists(file_path)
        
        badge_label = "Downloaded" if exists else "Not Found"
        badge_class = "badge-style badge bg-success text-light" if exists else "badge-style badge bg-danger text-light"
        
        if exists:
            found_count += 1
            # Load the slice
            data, err = load_dataset_slice(active_tab, prod_id, date_val, root_dir, bbox, stride=stride_val)
            if err:
                fig = go.Figure().update_layout(
                    xaxis=dict(visible=False), yaxis=dict(visible=False),
                    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="#f8fafc")
                )
                fig.add_annotation(text=err, showarrow=False, font=dict(color="red", size=14))
                meta_layout = html.Div([
                    html.Div(f"Error details: {err}", className="text-danger fw-bold small mb-2"),
                    render_metadata_layout(active_tab, prod_id, stats=None)
                ])
            else:
                if active_tab == "ssh":
                    lons, lats, values, colorscale, title_name, lc_coords = data
                else:
                    lons, lats, values, colorscale, title_name = data
                    lc_coords = None
                
                # Check for NaNs
                nan_mask = np.isnan(values)
                valid_values = values[~nan_mask]
                
                # Compute stats
                val_min = np.min(valid_values) if len(valid_values) > 0 else 0
                val_max = np.max(valid_values) if len(valid_values) > 0 else 0
                val_mean = np.mean(valid_values) if len(valid_values) > 0 else 0
                
                # Plot
                zmin = 20 if active_tab == "sst" else None
                zmax = 30 if active_tab == "sst" else None
                
                show_hover = "hover" in (hover_toggle or [])
                hover_info_val = None if show_hover else "skip"
                hover_tmpl_val = "Lon: %{x:.2f}°<br>Lat: %{y:.2f}°<br>Value: %{z:.3f}<extra></extra>" if show_hover else None
                
                fig = go.Figure(data=go.Heatmap(
                    z=values,
                    x=lons,
                    y=lats,
                    colorscale=colorscale,
                    zmin=zmin,
                    zmax=zmax,
                    hoverinfo=hover_info_val,
                    hovertemplate=hover_tmpl_val,
                    colorbar=dict(
                        title=dict(text=title_name, side="right"),
                        thickness=15,
                        len=0.85
                    ),
                ))
                
                # Add Loop Current overlay on SSH/ADT if computed
                if active_tab == "ssh" and lc_coords and len(lc_coords) > 0:
                    lc_lons = [pt[0] for pt in lc_coords]
                    lc_lats = [pt[1] for pt in lc_coords]
                    fig.add_trace(go.Scatter(
                        x=lc_lons,
                        y=lc_lats,
                        mode='lines',
                        name='Loop Current',
                        line=dict(color='#ef4444', width=3),
                        showlegend=True
                    ))
                
                fig.update_layout(
                    margin=dict(l=10, r=10, t=10, b=10),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#cbd5e1'),
                    dragmode='pan',
                    xaxis=dict(showgrid=True, gridcolor='#334155', zeroline=False),
                    yaxis=dict(showgrid=True, gridcolor='#334155', zeroline=False, scaleanchor="x", scaleratio=1),
                )
                meta_layout = render_metadata_layout(active_tab, prod_id, stats=(val_min, val_max, val_mean, values.shape))
        else:
            # Setup placeholder plot
            fig = go.Figure().update_layout(
                xaxis=dict(visible=False), yaxis=dict(visible=False),
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#f8fafc")
            )
            fig.add_annotation(text="No data available. Click Download to fetch.", showarrow=False, font=dict(color="#94a3b8", size=14))
            meta_layout = render_metadata_layout(active_tab, prod_id, stats=None)
            
        # Create Card Panel component for this product
        card_item = dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.Div([
                        html.Span(f"{prod_info['name']} ({date_str})", className="fw-bold text-white small"),
                        html.Span(badge_label, className=badge_class)
                    ], className="d-flex justify-content-between align-items-center")
                ], className="bg-transparent border-bottom border-secondary py-2"),
                dbc.CardBody([
                    dcc.Graph(
                        id={"type": "graph", "index": prod_id},
                        figure=fig,
                        config=PLOTLY_GRAPH_CONFIG,
                        style={"height": "380px"}
                    ),
                    html.Div(meta_layout)
                ])
            ], className="panel-card mb-4")
        ], md=col_width)
        
        panel_cards.append(card_item)
        
    # Render inside a Row
    panels_grid = dbc.Row(panel_cards)
    
    # Banner
    banner_content = html.Div([
        html.Span("Visualization Mode: ", className="text-white"),
        html.Strong("Dataset Dates", className="text-info me-3"),
        html.Span(f"Loaded Products: ", className="text-white"),
        html.Strong(f"{found_count} of {num_selected} selected", className="text-success" if found_count == num_selected else "text-warning")
    ], className="d-flex align-items-center w-100 justify-content-between")
    
    return full_log, banner_content, panels_grid

app.clientside_callback(
    """
    function(relayout_data_list, current_figures) {
        const ctx = window.dash_clientside.callback_context;
        if (!ctx.triggered || ctx.triggered.length === 0) {
            return current_figures;
        }
        
        const triggeredProp = ctx.triggered[0].prop_id;
        if (!triggeredProp.includes('.')) {
            return current_figures;
        }
        
        const triggeredIdStr = triggeredProp.split('.')[0];
        let triggeredId;
        try {
            triggeredId = JSON.parse(triggeredIdStr);
        } catch (e) {
            return current_figures;
        }
        
        const inputs = ctx.inputs_list[0];
        const triggeredIndex = inputs.findIndex(inp => {
            return inp.id && inp.id.index === triggeredId.index && inp.id.type === triggeredId.type;
        });
        
        if (triggeredIndex === -1) {
            return current_figures;
        }
        
        const relayout_data = relayout_data_list[triggeredIndex];
        if (!relayout_data) {
            return current_figures;
        }
        
        let update_x = false;
        let update_y = false;
        let x_range = null;
        let y_range = null;
        let x_auto = false;
        let y_auto = false;
        let is_auto = false;
        
        if (relayout_data['xaxis.autorange'] !== undefined || relayout_data['yaxis.autorange'] !== undefined) {
            is_auto = true;
            x_auto = relayout_data['xaxis.autorange'] !== false;
            y_auto = relayout_data['yaxis.autorange'] !== false;
        } else {
            if (relayout_data['xaxis.range'] !== undefined) {
                x_range = relayout_data['xaxis.range'];
                update_x = true;
            } else if (relayout_data['xaxis.range[0]'] !== undefined) {
                x_range = [relayout_data['xaxis.range[0]'], relayout_data['xaxis.range[1]']];
                update_x = true;
            }
            
            if (relayout_data['yaxis.range'] !== undefined) {
                y_range = relayout_data['yaxis.range'];
                update_y = true;
            } else if (relayout_data['yaxis.range[0]'] !== undefined) {
                y_range = [relayout_data['yaxis.range[0]'], relayout_data['yaxis.range[1]']];
                update_y = true;
            }
        }
        
        if (!is_auto && !update_x && !update_y) {
            return current_figures;
        }
        
        let any_change = false;
        const new_figures = current_figures.map((fig, idx) => {
            if (!fig) return fig;
            if (idx === triggeredIndex) {
                return fig;
            }
            
            const current_x_range = fig.layout && fig.layout.xaxis ? fig.layout.xaxis.range : undefined;
            const current_y_range = fig.layout && fig.layout.yaxis ? fig.layout.yaxis.range : undefined;
            const current_x_auto = fig.layout && fig.layout.xaxis ? fig.layout.xaxis.autorange : undefined;
            const current_y_auto = fig.layout && fig.layout.yaxis ? fig.layout.yaxis.autorange : undefined;
            
            let fig_needs_update = false;
            
            if (is_auto) {
                if (current_x_auto !== x_auto || current_y_auto !== y_auto) {
                    fig_needs_update = true;
                }
            } else {
                const tol = 1e-7;
                if (update_x) {
                    if (current_x_auto !== false || !current_x_range) {
                        fig_needs_update = true;
                    } else {
                        const diff_x0 = Math.abs(current_x_range[0] - x_range[0]);
                        const diff_x1 = Math.abs(current_x_range[1] - x_range[1]);
                        if (diff_x0 > tol || diff_x1 > tol) {
                            fig_needs_update = true;
                        }
                    }
                }
                if (update_y) {
                    if (current_y_auto !== false || !current_y_range) {
                        fig_needs_update = true;
                    } else {
                        const diff_y0 = Math.abs(current_y_range[0] - y_range[0]);
                        const diff_y1 = Math.abs(current_y_range[1] - y_range[1]);
                        if (diff_y0 > tol || diff_y1 > tol) {
                            fig_needs_update = true;
                        }
                    }
                }
            }
            
            if (fig_needs_update) {
                any_change = true;
                const updated_fig = JSON.parse(JSON.stringify(fig));
                if (!updated_fig.layout) updated_fig.layout = {};
                if (!updated_fig.layout.xaxis) updated_fig.layout.xaxis = {};
                if (!updated_fig.layout.yaxis) updated_fig.layout.yaxis = {};
                
                if (is_auto) {
                    updated_fig.layout.xaxis.autorange = x_auto;
                    updated_fig.layout.yaxis.autorange = y_auto;
                } else {
                    if (update_x) {
                        updated_fig.layout.xaxis.range = x_range;
                        updated_fig.layout.xaxis.autorange = false;
                    }
                    if (update_y) {
                        updated_fig.layout.yaxis.range = y_range;
                        updated_fig.layout.yaxis.autorange = false;
                    }
                }
                return updated_fig;
            }
            
            return fig;
        });
        
        if (!any_change) {
            return window.dash_clientside.no_update;
        }
        return new_figures;
    }
    """,
    Output({"type": "graph", "index": dash.dependencies.ALL}, "figure"),
    [Input({"type": "graph", "index": dash.dependencies.ALL}, "relayoutData")],
    [State({"type": "graph", "index": dash.dependencies.ALL}, "figure")],
    prevent_initial_call=True
)

# ----------------------------------------------------------------------
# 8. Start dashboard server
# ----------------------------------------------------------------------
if __name__ == '__main__':
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    print("Starting Dash Satellite Dashboard server on port 8050...")
    app.run(debug=True, host='127.0.0.1', port=8050)
