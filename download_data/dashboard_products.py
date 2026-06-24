"""Product metadata used by the local satellite data dashboard.

Download scripts should update this module when new dashboard variables or
products are added. The Dash app imports this metadata but does not perform
downloads itself.
"""

import datetime
import os

SATELLITE_PRODUCTS = {
    "sst": {
        "sst_mur_public": {
            "name": "JPL MUR SST v4.1 (Public ERDDAP)",
            "source": "NASA JPL / NOAA ERDDAP (No credentials)",
            "satellite_sensor": "Multi-sensor GHRSST (AMSR2, MODIS, AVHRR, VIIRS, in situ)",
            "processing_level": "L4",
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
            "satellite_sensor": "Multi-sensor GHRSST (AMSR2, MODIS, AVHRR, VIIRS, in situ)",
            "processing_level": "L4",
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
            "dataset_id": "MUR-JPL-L4-GLOB-v4.1",
            "default_date": "2026-05-05"
        },
        "sst_cmc_podaac": {
            "name": "GHRSST CMC L4 (PODAAC)",
            "source": "Canada Meteorological Center / PODAAC (Requires netrc)",
            "satellite_sensor": "Multi-sensor infrared (MetOp/NOAA AVHRR backbone)",
            "processing_level": "L4",
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
            "dataset_id": "CMC0.1deg-CMC-L4-GLOB-v3.0",
            "default_date": "2026-05-05"
        },
        "sst_odyssea_nrt": {
            "name": "Copernicus ODYSSEA SST L3 NRT (2021-Present)",
            "source": "Copernicus Marine Service (Requires credentials)",
            "satellite_sensor": "Multi-sensor SST fusion (VIIRS, AVHRR, SLSTR, AMSR2)",
            "processing_level": "L3",
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
            "satellite_sensor": "Multi-sensor SST fusion (VIIRS, AVHRR, SLSTR, AMSR2)",
            "processing_level": "L3",
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
        "sst_goes_abi": {
            "name": "GOES-19 ABI ACSPO SST L3C (GOES-East)",
            "source": "NASA PO.DAAC / NOAA STAR ACSPO (Requires netrc)",
            "satellite_sensor": "GOES-19 ABI (GOES-East, hourly L3C)",
            "processing_level": "L3C",
            "resolution": "0.02° (~2 km)",
            "period": "2025 - Present",
            "desc": "Hourly ABI sea-surface sub-skin temperature from GOES-East ACSPO L3C",
            "dir_rel": os.path.join("SST", "GOES_ABI"),
            "file_fmt": lambda d: f"GOES_ABI_SST_{d.year}-{d.month:02d}-{d.day:02d}_1200.nc",
            "var_name": "sea_surface_temperature",
            "coords": ("lon", "lat"),
            "colorscale": "Thermal",
            "unit": "Temperature (°C)",
            "download_type": "goes_abi_sst",
            "goes_product": "g19_l3c",
            "download_hour": 12,
            "default_date": "2026-05-05"
        },
        "sst_viirs_acspo_l2p": {
            "name": "VIIRS ACSPO L2P SST (JPSS SNPP/NOAA-20/21)",
            "source": "NASA PO.DAAC / NOAA STAR ACSPO (Requires netrc)",
            "satellite_sensor": "VIIRS on Suomi-NPP, NOAA-20, NOAA-21",
            "processing_level": "L2P",
            "resolution": "~0.75 km nadir (~1.5 km swath edge)",
            "period": "2012 - Present",
            "desc": "Merged daily JPSS VIIRS swath SST for sharp fronts and coastal detail",
            "dir_rel": os.path.join("SST", "VIIRS_ACSPO_L2P"),
            "file_fmt": lambda d: f"VIIRS_ACSPO_L2P_SST_{d.year}-{d.month:02d}-{d.day:02d}.nc",
            "var_name": "sea_surface_temperature",
            "coords": ("lon", "lat"),
            "colorscale": "Thermal",
            "unit": "Temperature (°C)",
            "download_type": "viirs_acspo_l2p",
            "swath_points": True,
            "default_date": "2026-05-05"
        },
        "sst_ostia_l4": {
            "name": "Copernicus OSTIA SST L4 (2007-Present)",
            "source": "Copernicus Marine Service (Requires credentials)",
            "satellite_sensor": "Sentinel-3 SLSTR / MetOp AVHRR multi-sensor",
            "processing_level": "L4",
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
            "satellite_sensor": "SMAP L-band radiometer",
            "processing_level": "L3",
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
        "sss_smap_coastwatch_daily": {
            "name": "NOAA CoastWatch SMAP NRT L3 Daily Mean SSS",
            "source": "NOAA NESDIS CoastWatch / STAR (No credentials)",
            "satellite_sensor": "SMAP L-band radiometer",
            "processing_level": "L3",
            "resolution": "0.25° x 0.25° (~60-70 km)",
            "period": "2015 - Present",
            "desc": "Daily-mean SMAP sea surface salinity without temporal smoothing",
            "dir_rel": os.path.join("SSS", "SMAP_CoastWatch_Daily"),
            "file_fmt": lambda d: f"SSS_SMAP_CoastWatch_Daily_{d.year}-{d.month:02d}-{d.day:02d}.nc",
            "var_name": "sss",
            "coords": ("lon", "lat"),
            "colorscale": "Haline",
            "unit": "Salinity (psu)",
            "download_type": "coastwatch_smap_sss_daily",
            "default_date": "2026-05-05"
        },
        "sss_smap_jpl": {
            "name": "SMAP JPL L3 SSS CAP 8-Day V5 (PODAAC)",
            "source": "NASA JPL CAP / PODAAC (Requires netrc)",
            "satellite_sensor": "SMAP L-band radiometer",
            "processing_level": "L3",
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
            "dataset_id": "SMAP_JPL_L3_SSS_CAP_8DAY-RUNNINGMEAN_V5",
            "default_date": "2026-05-05"
        },
        "sss_cmems_multiobs_my_daily": {
            "name": "Copernicus MultiObs SSS/SSD L4 MY Daily",
            "source": "Copernicus Marine Service (Requires credentials)",
            "satellite_sensor": "SMOS + SMAP + in situ blend",
            "processing_level": "L4",
            "resolution": "0.125° x 0.125° (~14 km)",
            "period": "1993 - 2024-12-15",
            "desc": "Daily multi-year reprocessed global analysed sea surface salinity and density",
            "dir_rel": os.path.join("SSS", "COPERNICUS_MULTIOBS_L4"),
            "file_fmt": lambda d: f"SSS_CMEMS_MULTIOBS_L4_MY_DAILY_{d.year}-{d.month:02d}-{d.day:02d}.nc",
            "var_name": "sos",
            "coords": ("longitude", "latitude"),
            "colorscale": "Haline",
            "unit": "Salinity (psu)",
            "download_type": "copernicus_marine",
            "dataset_id": "cmems_obs-mob_glo_phy-sss_my_multi_P1D",
            "version": "202311",
            "variables": ["sos", "sos_error", "dos", "dos_error", "sea_ice_fraction"],
            "default_date": "2019-05-05"
        },
        "sss_cmems_multiobs_my_monthly": {
            "name": "Copernicus MultiObs SSS/SSD L4 MY Monthly",
            "source": "Copernicus Marine Service (Requires credentials)",
            "satellite_sensor": "SMOS + SMAP + in situ blend",
            "processing_level": "L4",
            "resolution": "0.125° x 0.125° (~14 km)",
            "period": "1993 - 2024-12",
            "desc": "Monthly multi-year reprocessed global analysed sea surface salinity and density",
            "dir_rel": os.path.join("SSS", "COPERNICUS_MULTIOBS_L4"),
            "file_fmt": lambda d: f"SSS_CMEMS_MULTIOBS_L4_MY_MONTHLY_{d.year}-{d.month:02d}.nc",
            "var_name": "sos",
            "coords": ("longitude", "latitude"),
            "colorscale": "Haline",
            "unit": "Salinity (psu)",
            "download_type": "copernicus_marine",
            "dataset_id": "cmems_obs-mob_glo_phy-sss_my_multi_P1M",
            "version": "202311",
            "variables": ["sos", "sos_error", "dos", "dos_error", "sea_ice_fraction"],
            "default_date": "2019-05-01"
        },
        "sss_cmems_multiobs_nrt_daily": {
            "name": "Copernicus MultiObs SSS/SSD L4 NRT Daily",
            "source": "Copernicus Marine Service (Requires credentials)",
            "satellite_sensor": "SMOS + SMAP + in situ blend",
            "processing_level": "L4",
            "resolution": "0.125° x 0.125° (~14 km)",
            "period": "2021 - Present",
            "desc": "Daily near-real-time global analysed sea surface salinity and density",
            "dir_rel": os.path.join("SSS", "COPERNICUS_MULTIOBS_L4"),
            "file_fmt": lambda d: f"SSS_CMEMS_MULTIOBS_L4_NRT_DAILY_{d.year}-{d.month:02d}-{d.day:02d}.nc",
            "var_name": "sos",
            "coords": ("longitude", "latitude"),
            "colorscale": "Haline",
            "unit": "Salinity (psu)",
            "download_type": "copernicus_marine",
            "dataset_id": "cmems_obs-mob_glo_phy-sss_nrt_multi_P1D",
            "version": "202311",
            "variables": ["sos", "sos_error", "dos", "dos_error", "sea_ice_fraction"],
            "default_date": "2026-06-16"
        },
        "sss_cmems_multiobs_nrt_monthly": {
            "name": "Copernicus MultiObs SSS/SSD L4 NRT Monthly",
            "source": "Copernicus Marine Service (Requires credentials)",
            "satellite_sensor": "SMOS + SMAP + in situ blend",
            "processing_level": "L4",
            "resolution": "0.125° x 0.125° (~14 km)",
            "period": "2021 - Present",
            "desc": "Monthly near-real-time global analysed sea surface salinity and density",
            "dir_rel": os.path.join("SSS", "COPERNICUS_MULTIOBS_L4"),
            "file_fmt": lambda d: f"SSS_CMEMS_MULTIOBS_L4_NRT_MONTHLY_{d.year}-{d.month:02d}.nc",
            "var_name": "sos",
            "coords": ("longitude", "latitude"),
            "colorscale": "Haline",
            "unit": "Salinity (psu)",
            "download_type": "copernicus_marine",
            "dataset_id": "cmems_obs-mob_glo_phy-sss_nrt_multi_P1M",
            "version": "202311",
            "variables": ["sos", "sos_error", "dos", "dos_error", "sea_ice_fraction"],
            "default_date": "2026-05-01"
        }
    },
    "ssh": {
        "ssh_altimetry_public": {
            "name": "NOAA Altimetry Daily SLA (Public ERDDAP)",
            "source": "NOAA Laboratory for Satellite Altimetry (No credentials)",
            "satellite_sensor": "Multi-mission radar altimeters (Jason, Sentinel-3/6, SARAL, CryoSat-2)",
            "processing_level": "L3",
            "resolution": "0.25° x 0.25° (~25 km)",
            "period": "2017 - 2026-03-26",
            "desc": "Sea Surface Height Anomalies from Altimetry",
            "dir_rel": "AVISO",
            "file_fmt": lambda d: f"{d.year}-{d.month:02d}.nc",
            "var_name": "adt",
            "coords": ("longitude", "latitude"),
            "colorscale": "RdBu_r",
            "unit": "ADT / SLA (m)",
            "download_type": "erddap_ssh",
            "default_date": "2026-03-26"
        },
        "ssh_duacs_cmems": {
            "name": "Copernicus DUACS L4 SSH MY (1993-2022)",
            "source": "Copernicus Marine Service (Requires credentials)",
            "satellite_sensor": "Multi-mission nadir altimeters (Jason-3, Sentinel-3/6, SARAL, CryoSat-2, HY-2)",
            "processing_level": "L4",
            "resolution": "0.125° x 0.125° (~12.5 km)",
            "period": "1993 - 2022",
            "desc": "Global Ocean Gridded L4 Sea Surface Heights And Derived Variables Reprocessed 1993",
            "dir_rel": "AVISO",
            "file_fmt": lambda d: f"SSH_DUACS_L4_MY_{d.year}-{d.month:02d}.nc",
            "var_name": "adt",
            "coords": ("longitude", "latitude"),
            "colorscale": "RdBu_r",
            "unit": "Absolute Dynamic Topography (m)",
            "download_type": "copernicus_marine",
            "dataset_id": "cmems_obs-sl_glo_phy-ssh_my_allsat-l4-duacs-0.125deg_P1D",
            "version": "202411",
            "variables": ["adt", "err_sla", "err_ugosa", "err_vgosa", "flag_ice", "sla", "tpa_correction", "ugos", "ugosa", "vgos", "vgosa"],
            "lon_0_360": True,
            "default_date": "2019-05-05"
        },
        "ssh_duacs_nrt": {
            "name": "Copernicus DUACS L4 SSH/SLA/ADT NRT",
            "source": "Copernicus Marine Service (Requires credentials)",
            "satellite_sensor": "Multi-mission nadir altimeters (Jason-3, Sentinel-3/6, SARAL, CryoSat-2, HY-2)",
            "processing_level": "L4",
            "resolution": "0.125° x 0.125° (~12.5 km)",
            "period": "2022 - Present",
            "desc": "Global Ocean Gridded L4 Sea Surface Heights and Derived Variables NRT",
            "dir_rel": "AVISO",
            "file_fmt": lambda d: f"SSH_DUACS_L4_NRT_{d.year}-{d.month:02d}.nc",
            "var_name": "adt",
            "coords": ("longitude", "latitude"),
            "colorscale": "RdBu_r",
            "unit": "ADT / SLA (m)",
            "download_type": "copernicus_marine",
            "dataset_id": "cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.125deg_P1D",
            "version": "202506",
            "variables": ["adt", "err_sla", "err_ugosa", "err_vgosa", "flag_ice", "sla", "ugos", "ugosa", "vgos", "vgosa"],
            "lon_0_360": True,
            "default_date": "2026-05-05"
        },
        "ssh_duacs_swaths": {
            "name": "Copernicus DUACS L3 SSH Swaths (2022-Present)",
            "source": "Copernicus Marine Service (Requires credentials)",
            "satellite_sensor": "Multi-mission radar altimeters (along-track)",
            "processing_level": "L3",
            "resolution": "Along-track ~7 km",
            "period": "2022 - Present",
            "desc": "Global Ocean Along Track L3 Sea Surface Heights NRT",
            "dir_rel": "AVISO",
            "file_fmt": lambda d: f"SSH_DUACS_L3_SWATHS_{d.year}-{d.month:02d}.csv",
            "var_name": "sla_filtered",
            "coords": ("longitude", "latitude"),
            "colorscale": "RdBu_r",
            "unit": "Filtered Sea Level Anomaly (m)",
            "download_type": "copernicus_marine",
            "dataset_id": "cmems_obs-sl_glo_phy-ssh_nrt_al-l3-duacs_PT1S",
            "variables": ["sla_filtered", "sla_unfiltered"],
            "file_format": "csv",
            "time_span_day": True,
            "lon_0_360": False,
            "default_date": "2026-05-05"
        },
        "ssh_swot_karin_l2": {
            "name": "SWOT KaRIn L2 SSH (PO.DAAC)",
            "source": "NASA PO.DAAC (Requires netrc)",
            "satellite_sensor": "SWOT KaRIn wide-swath interferometric altimeter",
            "processing_level": "L2",
            "resolution": "~120 km swath; ~1 km x 1 km ocean SSH posting",
            "period": "2022-12-16 - Present",
            "desc": "Wide-swath 2-D KaRIn sea surface height for mesoscale Loop Current structure",
            "dir_rel": os.path.join("SSH", "SWOT_KARIN_L2"),
            "file_fmt": lambda d: f"SWOT_KARIN_L2_SSH_{d.year}-{d.month:02d}-{d.day:02d}.nc",
            "var_name": "ssh_karin",
            "coords": ("lon", "lat"),
            "colorscale": "RdBu_r",
            "unit": "KaRIn Sea Surface Height (m)",
            "download_type": "swot_karin_l2",
            "swath_points": True,
            "default_date": "2024-02-01"
        }
    },
    "chlora": {
        "chlor_viirs_public": {
            "name": "NOAA Daily VIIRS (Public ERDDAP)",
            "source": "NOAA Coastwatch / ERDDAP (No credentials)",
            "satellite_sensor": "JPSS VIIRS (SNPP, NOAA-20, NOAA-21)",
            "processing_level": "L3",
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
            "satellite_sensor": "Sentinel-3 OLCI",
            "processing_level": "L3",
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
            "satellite_sensor": "Sentinel-3 OLCI",
            "processing_level": "L3",
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
            "satellite_sensor": "Multi-sensor ocean colour (SeaWiFS, MODIS, MERIS/OLCI, VIIRS)",
            "processing_level": "L4",
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

PRODUCT_AVAILABILITY = {
    "sst_mur_public": "Daily; delayed analysis, typically available a few days after observation.",
    "sst_mur_podaac": "Daily; delayed analysis, typically available a few days after observation.",
    "sst_cmc_podaac": "Daily; near-real-time, typically available about 1 day after observation.",
    "sst_odyssea_nrt": "Daily; near-real-time, typically available about 1 day after observation.",
    "sst_odyssea_my": "Historical reprocessed archive; updated periodically, not near-real-time.",
    "sst_goes_abi": "Hourly near-real-time; GOES-East ACSPO L3C scenes are typically available within a few hours.",
    "sst_viirs_acspo_l2p": "Daily merged JPSS swaths; multiple passes per day over the Gulf of Mexico.",
    "sst_ostia_l4": "Daily; near-real-time, typically available about 1 day after observation.",
    "sss_smap_public": "8-day running product; available after the 8-day window and final processing.",
    "sss_smap_coastwatch_daily": "Daily near-real-time L3 mean; typically available within 24 hours of SMAP L2B data.",
    "sss_smap_jpl": "8-day running product; available after the 8-day window and processing.",
    "sss_cmems_multiobs_my_daily": "Daily multi-year reprocessed archive; current catalogue coverage ends on 2024-12-15.",
    "sss_cmems_multiobs_my_monthly": "Monthly multi-year reprocessed archive; current catalogue coverage ends in December 2024.",
    "sss_cmems_multiobs_nrt_daily": "Daily near-real-time extension; typically delayed by several days.",
    "sss_cmems_multiobs_nrt_monthly": "Monthly near-real-time extension; monthly averages are available after enough source data is processed.",
    "ssh_altimetry_public": "Daily; ERDDAP service currently advertises data through 2026-03-26.",
    "ssh_duacs_cmems": "Historical reprocessed archive; updated periodically, not near-real-time.",
    "ssh_duacs_nrt": "Daily near-real-time 0.125° L4 product; typically available within 1-2 days.",
    "ssh_duacs_swaths": "Along-track near-real-time; typically available within 1-2 days.",
    "ssh_swot_karin_l2": "21-day repeat orbit; Gulf of Mexico KaRIn swaths occur on pass-specific dates only.",
    "chlor_viirs_public": "Daily; near-real-time ocean color, typically available within 1-2 days.",
    "chlor_olci_300m": "Daily reprocessed archive; updated periodically, not same-day.",
    "chlor_olci_4km": "Daily reprocessed archive; updated periodically, not same-day.",
    "chlor_l4_gapfree": "Daily gap-free reprocessed product; updated periodically, not same-day.",
}

SATELLITE_SUMMARY = {
    "SST": {
        "title": "Sea Surface Temperature (SST)",
        "rows": [
            {
                "satellite": "VIIRS - SNPP, NOAA-20, NOAA-21",
                "instrument": "Visible Infrared Imaging Radiometer Suite",
                "dates": "2012 - present for SNPP; JPSS follow-ons active",
                "l3_resolution": "ACSPO L2P swath: ~0.75 km nadir, ~1.5 km at swath edge",
                "l4_resolution": "NOAA Geo-Polar blended L4: 0.05° (~5 km)",
                "source": "NOAA STAR ACSPO VIIRS L2P SST",
                "url": "https://coastwatch.noaa.gov/cwn/products/acspo-global-sst-viirs.html",
                "notes": "Best raw-ish science-ready SST for sharp fronts, coastal detail, and Loop Current boundaries."
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
                "satellite": "GOES-East (GOES-19, formerly GOES-16)",
                "instrument": "ABI",
                "dates": "GOES-16: 2017-2025; GOES-19 operational GOES-East from Apr 2025",
                "l3_resolution": "ACSPO ABI L3C hourly: 0.02° (~2 km) America region",
                "l4_resolution": "Used in NOAA Geo-Polar blended L4: 0.05° (~5 km)",
                "source": "NOAA STAR ACSPO GOES ABI SST",
                "url": "https://coastwatch.noaa.gov/cwn/products/acspo-global-sst-abi.html",
                "notes": "Geostationary infrared SST; high temporal resolution over the Gulf of Mexico."
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
                "l3_resolution": "CoastWatch NRT daily mean L3: 0.25° x 0.25° (~60-70 km); RSS/JPL 8-day: ~40-60 km",
                "l4_resolution": "Used in Copernicus multi-observation L4 SSS: 0.125°",
                "source": "NOAA CoastWatch SMAP NRT / NASA PO.DAAC SMAP RSS/JPL",
                "url": "https://coastwatch.noaa.gov/cwn/products/sea-surface-salinity-near-real-time-smap.html",
                "notes": "CoastWatch daily L3 is the best current choice for daily SSS without temporal smoothing."
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
                "l4_resolution": "DUACS gridded L4 NRT: 0.125° x 0.125° daily",
                "source": "EUMETSAT Sentinel-6 / Copernicus",
                "url": "https://www.eumetsat.int/sentinel-6",
                "notes": "Current reference altimetry mission."
            },
            {
                "satellite": "Sentinel-3A/B",
                "instrument": "SRAL radar altimeter",
                "dates": "2016/2018 - present",
                "l3_resolution": "DUACS along-track L3: 1 Hz (~7 km); some regional 5 Hz (~1 km) sampling",
                "l4_resolution": "DUACS gridded L4 NRT: 0.125° x 0.125° daily",
                "source": "Copernicus DUACS L3",
                "url": "https://data.marine.copernicus.eu/product/SEALEVEL_GLO_PHY_L3_MY_008_062/description",
                "notes": "Part of the operational multi-mission altimeter constellation."
            },
            {
                "satellite": "Jason-3, SARAL/AltiKa, CryoSat-2, HY-2 series and other nadir altimeters",
                "instrument": "Radar altimeters",
                "dates": "Mission-dependent; available in DUACS multi-mission processing",
                "l3_resolution": "DUACS along-track L3: 1 Hz (~7 km) global sampling",
                "l4_resolution": "DUACS all-satellite L4 MY: 0.125° daily",
                "source": "Copernicus DUACS L4 MY",
                "url": "https://data.marine.copernicus.eu/product/SEALEVEL_GLO_PHY_L4_MY_008_047/description",
                "notes": "Multi-year reprocessed L4 archive used by the dashboard."
            },
            {
                "satellite": "Jason-3, Sentinel-3/6, SARAL/AltiKa, CryoSat-2, HY-2 series and other nadir altimeters",
                "instrument": "Radar altimeters",
                "dates": "2022 - present operational NRT",
                "l3_resolution": "DUACS along-track L3: 1 Hz (~7 km) global sampling",
                "l4_resolution": "DUACS all-satellite L4 NRT: 0.125° x 0.125° daily",
                "source": "Copernicus DUACS L4 NRT",
                "url": "https://data.marine.copernicus.eu/product/SEALEVEL_GLO_PHY_L4_NRT_008_046/description",
                "notes": "Current near-real-time L4 SSH/SLA/ADT product for the dashboard."
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


def parse_date(date_str: str) -> datetime.date:
    """Parse an ISO ``YYYY-MM-DD`` string into a ``date``."""
    return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()


def get_product_date(prod_info: dict) -> datetime.date:
    """Return the default dashboard date for a product metadata entry."""
    return parse_date(prod_info.get("default_date", DEFAULT_FALLBACK_DATE))


def get_product_file_path(prod_info: dict, date_val: datetime.date, root_dir: str) -> str:
    """Build the expected on-disk path for a product on a given date."""
    file_name = prod_info["file_fmt"](date_val)
    return os.path.join(root_dir, prod_info["dir_rel"], file_name)


def get_best_local_product_date(prod_info: dict, root_dir: str) -> datetime.date:
    """Return the best local date hint for a product.

    TODO: Scan ``root_dir`` for existing files instead of using ``default_date``.
    """
    return get_product_date(prod_info)


def format_product_date_hint(prod_info: dict) -> str:
    """Format the default product date as ``YYYY-MM-DD`` for UI hints."""
    return get_product_date(prod_info).strftime("%Y-%m-%d")


def get_product_availability(product_id: str) -> str:
    """Return human-readable availability notes for a dashboard product id."""
    return PRODUCT_AVAILABILITY.get(product_id, "See source metadata for update cadence.")


def get_product_processing_level(prod_info: dict) -> str:
    """Return the GHRSST/Copernicus-style processing level label for a product.

    Args:
        prod_info: Product metadata dictionary from ``SATELLITE_PRODUCTS``.

    Returns:
        Processing level string such as ``L3`` or ``L4``.
    """
    return prod_info.get("processing_level", "—")


def get_product_satellite_sensor(prod_info: dict) -> str:
    """Return the satellite platform and instrument label for a product.

    Args:
        prod_info: Product metadata dictionary from ``SATELLITE_PRODUCTS``.

    Returns:
        Human-readable satellite/sensor description for the dashboard panel.
    """
    return prod_info.get("satellite_sensor", "—")

