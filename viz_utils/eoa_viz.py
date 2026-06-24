"""Cartopy-based map visualization for EOAS gridded and geospatial data."""

import os
from PIL import Image
import cv2
from os import listdir
from os.path import join

import matplotlib.pyplot as plt
import matplotlib
from matplotlib.colors import LogNorm
from io_utils.io_common import create_folder
from viz_utils.constants import PlotMode, BackgroundType
import pylab
import numpy as np
import cmocean
import shapely
import xarray

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy

def select_colormap(field_name: str):
    """Pick a cmocean colormap from a variable name heuristic.

    Args:
        field_name: Variable or product name (case-insensitive substring match).

    Returns:
        A ``cmocean`` colormap object, or ``None`` when no rule matches.
    """
    field_name = field_name.lower()
    if np.any([field_name.find(x) != -1 for x in ('ssh', 'srfhgt', 'adt','surf_el','sla')]):
        # cmaps_fields.append(cmocean.cm.deep_r)
        return cmocean.cm.curl
    elif np.any([field_name.find(x) != -1 for x in ('temp', 'sst', 'temperature')]):
        return cmocean.cm.thermal
    elif np.any([field_name.find(x) != -1 for x in ('vorticity', 'vort')]):
        return cmocean.cm.curl
    elif np.any([field_name.find(x) != -1 for x in ('salin', 'sss', 'sal')]):
        return cmocean.cm.haline
    elif np.any([field_name.find(x) != -1 for x in ('chlor-a', 'chlora', 'dchl', 'nchl','chl')]):
        return cmocean.cm.algae
    elif field_name.find('error') != -1:
        return cmocean.cm.diff
    elif field_name.find('binary') != -1:
        return cmocean.cm.oxy
    elif np.any([field_name.find(x) != -1 for x in ('u_', 'v_', 'u-vel.', 'v-vel.','velocity','ugos','vgos')]):
        return cmocean.cm.speed


class EOAImageVisualizer:
    """Matplotlib/Cartopy visualizer for EOAS map products.

    Supports xarray datasets, numpy arrays, and depth/time stacks. Configure
    display options via constructor kwargs (stored as ``_attr`` properties).

    Example::

        viz = EOAImageVisualizer(
            disp_images=True,
            output_folder="output",
            lats=lats,
            lons=lons,
        )
    """
    # ------- 'Global attributes' defined at init ------------
    _COLORS = ['y', 'r', 'c', 'b', 'g', 'w', 'k', 'y', 'r', 'c', 'b', 'g', 'w', 'k']
    _figsize = 8
    _font_size = 30
    _units = ''
    _max_imgs_per_row = 4
    _eoas_pyutils_path =  './eoas_pyutils'# This is the path where the eoas_utils folder is stored with respect to the main project
    _background = BackgroundType.BLUE_MARBLE_LR  # Select the background to use
    _auto_colormap = True  # Selects the colormap based on the name of the field
    _show_var_names = False  # Includes the name of the field name in the titles
    _contourf = False  # When plotting non-regular grids and need precision
    _additional_polygons = []  # MUST BE SHAPELY GEOMETRIES In case we want to include additional polygons in the plots (all of them)
    _coastline = True # If we want to display the coastline
    _land = False # If we want to display the land
    _ocean = False # If we want to display the ocean
    # ------ 'Local' attributes defined at each plot function
    _mincbar = None  # User can set a min and max colorbar values to 'force' same color bar to all plots
    _maxcbar  = None
    _flip_data = True
    # If you want to add a streamplot of a vector field. It must be a dictionary with keys x,y,u,v
    # and optional density, color, cmap, arrowsize, arrowstyle, minlength
    _vector_field = None

    # vizobj = EOAImageVisualizer(disp_images=True, output_folder='output',
    #                                 lats=[lats],lons=[lons])
    def __init__(self, disp_images=True, output_folder='output',
                 lats=[-90,90], lons =[-180,180],
                 projection=ccrs.PlateCarree(), **kwargs):
        """Initialize map extent, projection, and optional style overrides.

        Args:
            disp_images: When ``False``, figures are closed instead of shown.
            output_folder: Directory for saved PNG outputs.
            lats: Latitude extent as min/max or coordinate vector.
            lons: Longitude extent as min/max or coordinate vector. Values
                above 180 are wrapped by subtracting 360.
            projection: Cartopy CRS for subplot creation.
            **kwargs: Additional ``_name`` attributes (e.g. ``background``).
        """
        self._disp_images = disp_images
        self._output_folder = output_folder
        self._projection = projection
        if np.amax(lons) > 180:
            lons = lons - 360
        bbox = self.getExtent(lats, lons)
        self._extent = bbox
        self._lats = lats
        self._lons = lons
        self._fig_prop = (bbox[1]-bbox[0])/(bbox[3]-bbox[2])
        self._contour_labels = False
        for arg_name, arg_value in kwargs.items():
            self.__dict__["_" + arg_name] = arg_value
            # print(f'{"_" + arg_name} = {self.__dict__["_" + arg_name]}')

    def __getattr__(self, attr):
        '''Generic getter for all the properties of the class'''
        return self.__dict__["_" + attr]

    def __setattr__(self, attr, value):
        '''Generic setter for all the properties of the class'''
        self.__dict__["_" + attr] = value

    def add_colorbar(self, fig, im, ax, show_color_bar, label=""):
        # https://matplotlib.org/api/_as_gen/matplotlib.pyplot.colorbar.html
        if show_color_bar:
            font_size_cbar = self._font_size * .5
            # TODO how to make this automatic and works always
            cbar = fig.colorbar(im, ax=ax, shrink=.7)
            cbar.ax.tick_params(labelsize=font_size_cbar)
            if label != "":
                cbar.set_label(label, fontsize=font_size_cbar*1.2)
            else:
                cbar.set_label(self._units, fontsize=font_size_cbar*1.2)

    def plot_slice_eoa(self, c_img, ax, cmap='gray', mode=PlotMode.RASTER, mincbar=None, maxcbar=None, norm=None) -> None:
        """
        Plots a 2D img for EOA data.
        :param c_img: 2D array
        :param ax: geoaxes
        :return:
        """
        c_ax = ax
        if self._flip_data:
            origin = 'lower'
        else:
            origin = 'upper'

        if (norm is not(None)) and (isinstance(norm, (int, float, complex))) and np.isnan(norm):
            norm = None

        if self._background == BackgroundType.CARTO_DEF:
            c_ax.stock_img()
        elif self._background == BackgroundType.WHITE:
            ax.set_facecolor("white")
        elif self._background == BackgroundType.BLACK:
            ax.set_facecolor("black")
        elif self._background == BackgroundType.GREY:
            ax.set_facecolor("grey")
        elif self._background == BackgroundType.NONE:
            print("No background")
        else:
            if self._background == BackgroundType.BLUE_MARBLE_LR:
                img = plt.imread(join(self._eoas_pyutils_path,'viz_utils/imgs/bluemarble.png'))
            if self._background == BackgroundType.BLUE_MARBLE_HR:
                img = plt.imread(join(self._eoas_pyutils_path,'viz_utils/imgs/bluemarble_5400x2700.jpg'))
            if self._background == BackgroundType.TOPO:
                img = plt.imread(join(self._eoas_pyutils_path,'viz_utils/imgs/etopo.png'))
            if self._background == BackgroundType.BATHYMETRY:
                img = plt.imread(join(self._eoas_pyutils_path,'viz_utils/imgs/bathymetry_3600x1800.jpg'))
            # If img is not defined, then it will not plot the background
            if 'img' in locals():
                im = c_ax.imshow(img, origin='upper', extent=(-180,180,-90,90), transform=ccrs.PlateCarree())

        if mode == PlotMode.RASTER or mode == PlotMode.MERGED:
            if self._contourf:
                if norm is not None:
                    im = c_ax.contourf(self._lons, self._lats, c_img, 128, cmap=cmap, extent=self._extent, norm=norm)
                else:
                    im = c_ax.contourf(self._lons, self._lats, c_img, 128, cmap=cmap, extent=self._extent)
            else:
                if mincbar is None: 
                    im = c_ax.imshow(c_img, extent=self._extent, origin=origin, cmap=cmap, transform=self._projection, norm=norm)
                else:
                    if norm is not None:
                        print(f"Warning, using norm and mincbar at the same time is not recommended. Ignoring mincbar.")
                        im = c_ax.imshow(c_img, extent=self._extent, origin=origin, cmap=cmap, transform=self._projection, norm=norm)
                    else:
                        im = c_ax.imshow(c_img, extent=self._extent, origin=origin, cmap=cmap, vmin=mincbar, vmax=maxcbar, transform=self._projection, norm=norm)


        if mode == PlotMode.CONTOUR or mode == PlotMode.MERGED:
            c_ax.set_extent(self.getExtent(list(self._lats), list(self._lons)))
            if mode == PlotMode.CONTOUR:
                im = c_ax.contour(c_img, extent=self._extent, transform=self._projection)
            if mode == PlotMode.MERGED:
                if self._contour_labels:
                    im = c_ax.contour(c_img, self._contour_labels, colors='r', extent=self._extent, transform=self._projection)
                else:
                    im = c_ax.contour(c_img, extent=self._extent, transform=self._projection)

        if len(self._additional_polygons) > 0:
            pol_lats = []
            pol_lons = []
            for c_polygon in self._additional_polygons:
                if isinstance(c_polygon, shapely.geometry.linestring.LineString) or isinstance(c_polygon, shapely.geometry.linestring.Point):
                    x, y = c_polygon.xy
                elif isinstance(c_polygon, shapely.geometry.polygon.Polygon):
                    x, y = c_polygon.exterior.xy
                elif isinstance(c_polygon, shapely.geometry.multipoint.MultiPoint):
                    # TODO how to get these values more efficiently (and in one line)
                    x = [p.x for p in c_polygon.geoms]
                    y = [p.y for p in c_polygon.geoms]
                pol_lats += y
                pol_lons += x
                if isinstance(c_polygon, shapely.geometry.linestring.Point) or isinstance(c_polygon, shapely.geometry.multipoint.MultiPoint):
                    c_ax.scatter(x, y, transform=self._projection, c='r')
                else:
                    c_ax.plot(x,y, transform=self._projection, c='r', linewidth=3, linestyle='--')

            #  Adds a threshold to the plot to see the polygons
            c_ax.set_extent(self.getExtent(list(self._lats) + pol_lats, list(self._lons) + pol_lons, 0.5))

        if self._coastline:
            c_ax.coastlines()

        if self._land:
            c_ax.add_feature(cartopy.feature.LAND, edgecolor='black')
            
        if self._ocean:
            c_ax.add_feature(cartopy.feature.OCEAN, edgecolor='black')

        if self._vector_field != None:
            try:
                u = self._vector_field['u']
                v = self._vector_field['v']
                x = self._vector_field['x']
                y = self._vector_field['y']
                vec_keys = self._vector_field.keys()
                c = 'r'
                density = 1
                linewidth = 3
                vec_cmap = cmocean.cm.solar
                if 'color' in vec_keys:
                    c = self._vector_field['color']
                if 'density' in vec_keys:
                    density = self._vector_field['density']
                if 'linewidth' in vec_keys:
                    linewidth = self._vector_field['linewidth']
                if 'cmap' in vec_keys:
                    vec_cmap = self._vector_field['cmap']
                c_ax.set_extent(self.getExtent(list(self._lats), list(self._lons)))
                c_ax.streamplot(x, y, u, v, transform=self._projection, density=density, color=c,
                                cmap=vec_cmap, linewidth=linewidth)

            except Exception as e:
                print(F"Couldn't add vector field e:{e}")


        gl = c_ax.gridlines(draw_labels=True, color='grey', alpha=0.5, linestyle='--')
        # gl.xlabel_style = {'size': self._font_size/2, 'color': '#aaaaaa', 'weight':'bold'}
        font_coords = {'size': self._font_size*.6}
        gl.xlabel_style = font_coords
        gl.ylabel_style = font_coords
        gl.top_labels = False
        gl.right_labels = False

        return im

    def get_proper_size(self, rows, cols):
        """
        Obtains the proper size for a figure.
        :param rows: how many rows will the figure have
        :param cols: how many colswill the figure have
        :param prop: Proportion is the proportion to use w/h
        :return:
        """
        if rows == 1:
            return self._figsize * cols * self._fig_prop, self._figsize
        else:
            return self._figsize * cols * self._fig_prop, self._figsize * rows

    def _close_figure(self):
        """Depending on what is disp_images, the figures are displayed or just closed"""
        if self._disp_images:
            plt.show()
        else:
            plt.close()

    def getExtent(self, lats, lons, expand_ext=0.0):
        '''
        Obtains the bbox of the coordinates. If included threshold then increases the bbox in all directions with that thres
        Args:
            lats:
            lons:
            inc_threshold:

        Returns:

        '''
        minLat = np.amin(lats).item() - expand_ext
        maxLat = np.amax(lats).item() + expand_ext
        minLon = np.amin(lons).item() - expand_ext
        maxLon = np.amax(lons).item() + expand_ext
        bbox = (minLon, maxLon, minLat, maxLat)
        return bbox

    def add_roads(self, ax):
        # Names come from: https://www.naturalearthdata.com/features/
        # -- Add states
        roads = cfeature.NaturalEarthFeature(
            category='cultural',
            name='roads',
            scale='10m',
            facecolor='none')

        ax.add_feature(roads, edgecolor='black')
        return ax

    def add_states(self, ax):
        # Names come from: https://www.naturalearthdata.com/features/
        # -- Add states
        states_provinces = cfeature.NaturalEarthFeature(
            category='cultural',
            name='admin_1_states_provinces_lines',
            scale='50m',
            facecolor='none')

        ax.add_feature(states_provinces, edgecolor='gray')
        return ax

    def plot_scatter_data(self, lats=None, lons=None, bbox=None, s=1, c='blue', cmap='plasma', title=''):
        '''
        This function plots points in a map
        :param bbox:
        :return:
        '''
        if bbox is None:
            bbox = (-180, 180, -90, 90)
        if lats is None:
            lats = self.lats
        if lons is None:
            lons = self.lons

        fig, ax = plt.subplots(1, 1, figsize=(self._figsize, self._figsize), subplot_kw={'projection': ccrs.PlateCarree()})
        ax.set_extent(bbox)  # If we do not set this, it will cropp it to the limits of the locations
        ax.gridlines()
        im = ax.scatter(lons, lats, s=s, c=c, cmap=cmap)
        fig.colorbar(im, ax=ax, shrink=0.7)
        ax.coastlines(resolution='10m')
        plt.title(title)
        plt.show()

    def plot_4d_data_npdict(self, variables_dic:list, var_names:list, times=[], z_levels= [], title='',
                          file_name_prefix='', cmap=None, z_names = [],
                          show_color_bar=True, plot_mode=PlotMode.RASTER, mincbar=None, maxcbar=None, norm=None):
        """
        Plots multiple z_levels for multiple fields.
        It assumes the dimensions on the fields are (time, depth, lat, lon)
        It calls plot_3d for every timestep, to it generates one image per timestep
        It assumes all the fields have the same number of timesteps
        Args:
            variables_dic: numpy dictionary or xarray df with the fields
            var_names: names of the fiels to be plotted
            times: an index array of the times to be plotted
            z_levels: which depth levels to plot
            title: title of the plots
            file_name_prefix: a file_prefix to use
            cmap: a colormap to be used for all the fields
            show_color_bar: if we want to display the colorbar
            plot_mode:
            mincbar:
            maxcbar:
        Returns:
        """
        if len(times) == 0:
            times = range(variables_dic[var_names[0]].shape[0])  # Assuming first index are the times
            # Verify each timestep is available on all fields
            for c_field in var_names:
                c_field = variables_dic[c_field]
                assert c_field.shape[0] >= len(times)

        for c_time in times:
            title = F"Time: {c_time} {title}"
            file_name_prefix = F"{c_time}_{file_name_prefix}"
            c_time_vars_dic = {var_name:variables_dic[var_name][c_time,:,:,:] for var_name in var_names}
            self.plot_3d_data_npdict(c_time_vars_dic, var_names, z_levels, title,
                                    file_name_prefix, cmap, z_names, show_color_bar,
                                    plot_mode, mincbar, maxcbar, norm=norm)

    def plot_3d_data_npdict(self, variables_dic:list, var_names:list, z_levels= [], title='',
                          file_name_prefix='', cmap=None, z_names = [],
                          show_color_bar=True, plot_mode=PlotMode.RASTER, mincbar=None, maxcbar=None, norm=None):
        """
        Plots multiple z_levels for multiple fields.
        It assumes the dimensions on the fields are (depth, lat, lon)
        Main plotting function. All the other functions call this one.
        Args:
        Returns:
        """
        create_folder(self._output_folder)
        orig_cmap = cmap

        # If the user do not requires any z-leve, then all are plotted
        if len(z_levels) == 0:
            z_levels = range(variables_dic[var_names[0]].shape[0])

        cols = np.min((self._max_imgs_per_row, len(var_names)))
        if cols == len(var_names):
            rows = len(z_levels)
        else:
            rows = int(len(z_levels) * np.ceil(len(var_names)/cols))

        fig, _axs = plt.subplots(rows, cols,
                                 figsize=self.get_proper_size(rows, cols),
                                 subplot_kw={'projection': self._projection})

        for c_zlevel, c_slice in enumerate(z_levels):  # Iterates over the z-levels
            # Verify the index of the z_levels are the original ones.
            if len(z_names) != 0:
                c_slice_txt = z_names[c_slice]
            else:
                c_slice_txt = c_slice

            c_mincbar = None
            c_maxcbar = None
            c_norm = None
            for idx_var, c_var in enumerate(var_names): # Iterate over the fields
                if rows*cols == 1:  # Single figure
                    ax = _axs
                else:
                    ax = _axs.flatten()[c_zlevel*len(var_names) + idx_var]

                # Here we chose the min and max colorbars for each field
                if type(mincbar) is list or type(mincbar) is np.ndarray:
                    c_mincbar = mincbar[idx_var]
                else:
                    c_mincbar = mincbar
                if type(maxcbar) is list or type(maxcbar) is np.ndarray:
                    if maxcbar[idx_var] != None:
                        c_maxcbar = maxcbar[idx_var]
                else:
                    c_maxcbar = maxcbar

                if type(norm) is list or type(norm) is np.ndarray:
                    c_norm = norm[idx_var]
                else:
                    c_norm = norm

                # By default we select the colorbar from the name of the variable
                if self._auto_colormap and orig_cmap is None:
                    cmap = select_colormap(c_var)
                else:
                    # If there is an array of colormaps we select the one for this field
                    if type(orig_cmap) is list:
                        cmap = orig_cmap[idx_var]
                    else:
                        # If it is just one cmap, then we use it for all the fields
                        cmap = orig_cmap

                im = self.plot_slice_eoa(variables_dic[c_var][c_slice,:,:], ax, cmap=cmap, mode=plot_mode,
                                         mincbar=c_mincbar, maxcbar=c_maxcbar, norm=c_norm)

                if self._show_var_names:
                    c_title = F'{var_names[idx_var]} {title}'
                else:
                    c_title = F'{title}'

                if len(z_levels) > 1:
                    c_title += F"Z - level: {c_slice_txt}"

                ax.set_title(c_title, fontsize=self._font_size)

                self.add_colorbar(fig, im, ax, show_color_bar)

        plt.tight_layout(pad=.5)
        file_name = F'{file_name_prefix}'
        pylab.savefig(join(self._output_folder, F'{file_name}.png'), bbox_inches='tight', dpi=300)
        self._close_figure()

    def plot_3d_data_np(self, np_variables:list, var_names:list, rot_90=False, flip_data=False, **kwargs):
        '''
        Wrapper function to receive raw 2D numpy data. It calls the 'main' function for 3D plotting
        :param np_variables: Numpy variables. They can be with shape [fields, x, y]  or just a single field with shape [x,y]
        :param var_names:
        :param title:
        :param file_name_prefix:
        :param cmap:
        :param flip_data:
        :param rot_90:
        :param show_color_bar:
        :param plot_mode:
        :param mincbar:
        :param maxcbar:
        :return:
        '''
        npdict_3d = {}
        for i, field_name in enumerate(var_names):
            c_np_data = np_variables[i]  # Single field

            if rot_90:
                c_np_data = np.rot90(c_np_data)
            if flip_data:
                c_np_data = np.flip(np.flip(c_np_data), axis=1)
            npdict_3d[field_name] = c_np_data
        
        self.plot_3d_data_npdict(npdict_3d, var_names, **kwargs)


    def plot_2d_data_xr(self, xr_ds:list, var_names:list, title='',
                            file_name_prefix='', cmap='viridis',  show_color_bar=True, plot_mode=PlotMode.RASTER, 
                            mincbar=None, maxcbar=None, norm=None):
        '''
        Wrapper function to receive an xarray with 2D fields. It calls the 'main' function for 3D plotting
        :param xr_ds:
        :param var_names:
        :param title:
        :param file_name_prefix:
        :param cmap:
        :param flip_data:
        :param rot_90:
        :param show_color_bar:
        :param plot_mode:
        :param mincbar:
        :param maxcbar:
        :return:
        '''
        npdict_3d = {}
        for i, field_name in enumerate(var_names):
            npdict_3d[field_name] = np.expand_dims(xr_ds[field_name], axis=0)
        self.plot_3d_data_npdict(npdict_3d, var_names, z_levels=[0], title=title,
                        file_name_prefix=file_name_prefix, cmap=cmap, z_names = [],
                        show_color_bar=show_color_bar, plot_mode=plot_mode, mincbar=mincbar, maxcbar=maxcbar, norm=norm)

    def plot_2d_data_np(self, np_variables:list, var_names:list, title='',
                            file_name_prefix='', cmap=None,  flip_data=False,
                            rot_90=False, show_color_bar=True, plot_mode=PlotMode.RASTER, mincbar=None, maxcbar=None, norm=None):
        '''
        Wrapper function to receive a list of 2D numpy data. It calls the 'main' function for 3D plotting
        :param np_variables: Numpy variables. They can be with shape [fields, x, y]  or just a single field with shape [x,y]
        :param var_names:
        :param title:
        :param file_name_prefix:
        :param cmap:
        :param flip_data:
        :param rot_90:
        :param show_color_bar:
        :param plot_mode:
        :param mincbar:
        :param maxcbar:
        :return:
        '''
        npdict_3d = {}
        for i, field_name in enumerate(var_names):
            if isinstance(np_variables, list):
                c_np_data = np_variables[i]  # Single field
            else:
                if len(np_variables.shape) == 3:
                    c_np_data = np_variables[i, :, :]
                else:
                    c_np_data = np_variables[i]  # Single field

            if rot_90:
                c_np_data = np.rot90(c_np_data)
            if flip_data:
                c_np_data = np.flip(np.flip(c_np_data), axis=1)
            npdict_3d[field_name] = np.expand_dims(c_np_data, axis=0)

        self.plot_3d_data_npdict(npdict_3d, var_names, z_levels=[0], title=title,
                        file_name_prefix=file_name_prefix, cmap=cmap, z_names = [],
                        show_color_bar=show_color_bar, plot_mode=plot_mode, mincbar=mincbar, maxcbar=maxcbar, norm=norm)

    def make_video_from_images(self, input_folder, output_file, fps=24):
        files = listdir(input_folder)
        files.sort()

        print(F"Generating video file: {output_file}")
        out_video = -1
        for i, file_name in enumerate(files[0:36]):
            if i % 10 == 0:
                print(F"Adding file # {i}: {file_name}")
            c_file = join(input_folder, file_name)
            im = Image.open(c_file)
            np_im = np.asarray(im)[:, :, :3]
            if i == 0:
                video_size = (np_im.shape[1], np_im.shape[0])
                out_video = cv2.VideoWriter(output_file, cv2.VideoWriter_fourcc(*'mp4v'), fps, video_size, True)
            out_video.write(np_im[:, :, ::-1])

        out_video.release()
        cv2.destroyAllWindows()
        print("Done! yeah babe!")
