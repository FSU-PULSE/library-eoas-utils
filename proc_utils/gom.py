"""Gulf of Mexico Loop Current extraction from altimetry and cached contours."""

from scipy.interpolate import interp1d
from skimage import measure
from matplotlib import path
import numpy as np
import pickle
from os.path import join

# Gulf of Mexico boundary polygon in [lon, lat] order (matplotlib Path convention).
gom_bnd = np.array([
    [-87.5, 21.15], [-84.15, 22.35], [-82.9, 22.9], [-81, 22.9], [-81, 27],
    [-82.5, 32.5], [-76.5, 32.5], [-76.5, 16.5], [-90, 16.5], [-87.5, 21.15],
])
gom_path = path.Path(gom_bnd)


def change_units(cc: list, lon: np.ndarray, lat: np.ndarray) -> list:
    """Map skimage contour pixel indices to geographic lon/lat coordinates.

    ``measure.find_contours`` returns row/column indices; this function linearly
    interpolates them onto the provided coordinate axes.

    Args:
        cc: List of contour arrays with shape ``(n_points, 2)`` in index space.
        lon: 1-D longitude coordinates aligned with the image x-axis.
        lat: 1-D latitude coordinates aligned with the image y-axis.

    Returns:
        List of contour arrays with shape ``(n_points, 2)`` as ``[lat, lon]``.

    Side effects:
        Prints a message and skips contours that fail interpolation.
    """
    flon = interp1d(np.arange(0, len(lon)), lon)
    flat = interp1d(np.arange(0, len(lat)), lat)
    newcc = []
    for cci in cc:
        try:
            t = np.zeros(cci.shape)
            t[:, 0] = flat(cci[:, 0])
            t[:, 1] = flon(cci[:, 1])
            newcc.append(t)
        except Exception as e:
            print(F"Failed for {cci} error: {e}")
    return newcc


def lc_from_ssh(
    ssh: np.ndarray,
    lon: np.ndarray,
    lat: np.ndarray,
    mean_adt: float = 0.35869857,
):
    """Extract Loop Current boundary positions from sea-surface height.

    Follows altimetry practice where ADT anomalies are referenced to a mean
    field and a fixed contour level (0.17 m) isolates the Loop Current edge.
    See DUACS altimetry FAQ for background on SSH/ADT products.

    Args:
        ssh: 2-D absolute dynamic topography or SSH field, shape ``(n_lat, n_lon)``.
        lon: 1-D longitude coordinates.
        lat: 1-D latitude coordinates.
        mean_adt: Mean ADT offset subtracted before contouring (meters).

    Returns:
        ``zip`` iterator of ``(lon, lat)`` pairs along the retained contour(s).
        Up to two longest contours inside the Gulf are concatenated.
        Contours fully inside ``gom_bnd`` or west of -89° longitude are removed
        as non-Loop-Current features. Closed loops shorter than 0.5° are treated
        as eddies and discarded.

    Reference:
        https://duacs.cls.fr/faq/what-are-the-product-specification/different-sea-surface-heights-used-in-altimetry/
    """
    ssh = ssh - mean_adt
    cco = measure.find_contours(ssh, 0.17, fully_connected='low', positive_orientation='low')
    cc = change_units(cco, lon, lat)
    # Remove contour that are eddies
    for i in range(len(cc) - 1, -1, -1):
        cci = cc[i]
        if np.linalg.norm(cci[0] - cci[-1]) < 0.5:  # presence of a loop
            del cc[i]

    # Remove contour that are outside of the Gom
    for i in range(len(cc) - 1, -1, -1):
        cci = cc[i]
        if np.all(gom_path.contains_points(cci)):  # carribbean or atlantic ocean
            del cc[i]
        elif np.all(cci[:, 1] < -89):  # contour in the western gom
            del cc[i]
        elif len(cci) < 25:  # non-useful little contour
            del cc[i]

    indexes = [0]
    if len(cc) >= 2:
        indexes = [0, 1]
    lc_lats = np.concatenate([np.flip(cc[i][:, 0]) for i in indexes])
    lc_lons = np.concatenate([np.flip(cc[i][:, 1]) for i in indexes])
    pos = zip(lc_lons, lc_lats)
    return pos


def lc_from_date(
    c_date,
    folder: str = "/unity/f1/ozavala/DATA/GOFFISH/AVISO/LC",
):
    """Load a precomputed Loop Current contour pickle for a calendar date.

    Args:
        c_date: ``datetime.date`` (or compatible) with ``year``, ``month``, and
            ``day`` attributes.
        folder: Root directory containing ``YYYY/YYYY-MM-DD.pkl`` files.

    Returns:
        Unpickled contour object stored by the batch LC pipeline
        (see ``compute_lc_for_aviso.py``).
    """
    fname = join(folder, str(c_date.year), F"{c_date.year}-{c_date.month:02d}-{c_date.day:02d}.pkl")
    with open(fname, 'rb') as f:
        data = pickle.load(f)

    return data
