from astropy.io import fits
import astropy.units as u
from numpy import ma
import numpy as np
from lmfit import models

from .data import Data2D
from .world import World
from .plotter import ImPlotter, get_plot_norm, get_plot_extent

# a running line list

lines = {
        'OI6300':   [6300.304, 'Angstrom', r'$[\mathrm{OI}]\lambda 6300\AA$'],
        'OI6363':   [6363.777, 'Angstrom', r'$[\mathrm{OI}]\lambda 6363\AA$'],
        'NII6548':  [6548.04, 'Angstrom', r'$[\mathrm{NII}]\lambda 6548\AA$'],
        'NII6583':  [6583.46,  'Angstrom', r'$[\mathrm{NII}]\lambda 6583\AA$'],
        'HAlpha':   [6562.8,  'Angstrom', r'$\mathrm{H}\alpha$'],
        'HBeta':    [4861.325,  'Angstrom', r'$\mathrm{H}\beta$'],
        'SII6716':  [6716.44,  'Angstrom', r'$[\mathrm{SII}]\lambda 6716\AA$'],
        'SII6731':  [6730.81,  'Angstrom', r'$[\mathrm{SII}]\lambda 6730\AA$'],
        'CaII7291': [7291.47, 'Angstrom', r'$[\mathrm{CaII}]\lambda 7291\AA$'],
        'CaII7324': [7323.89, 'Angstrom', r'$[\mathrm{CaII}]\lambda 7324\AA$']
}

class PVSlice(Data2D):

    '''
    This is to just manage the 2d data shit, but it might
    end up being completely superfluous. We'll find out.
    '''

    def spectral_window(self, vmin, vmax=None, unit = None):
        '''
        Get a small view of the velocity/wavelength range.

        Parameters
        -----------
        vmin : float
            lower bound; if vmax is None, only a single pixel will be returned
        vmax : float or None
            upper bound of the view range
        unit : `astropy.units.Unit` or None
            if unit is None, vmin and vmax will be treated as pixels! otherwise,
            give it a velocity or wavelength value

        Returns
        --------
        out : `telassar.PVSlice` object
        '''

        if self.world.spectral_unit is None:
            raise ValueError("We need coordinates along the spectral direction")

        if vmax is None:
            vmax = vmin

        if unit is None:
            pmin = max(0, int(vmin + 0.5))
            pmax = min(self.shape[1], int(vmax + 0.5))

        else:
            pmin = max(0, self.world.wav2pix(vmin, nearest=True))
            pmax = min(self.shape[1], self.world.wav2pix(vmax, nearest = True) + 1)

        return self[:, pmin:pmax]

    def spatial_window(self, amin, amax = None, unit = None):
        '''
        Return a view of a spatial window

        Parameters
        ----------
        amin : float
            the lower bound of the view; assumed in arcseconds
        amax : float or None
            the upper bound of the view. if None, only a single pixel value will
            be returned (in arcseconds). NOTE: this pixel value will span the
            entire wavelength range!
        unit : `astropy.units.Unit` or None
            if no unit is specified, values will be treated like pixels. otherwise,
            give it a u.arcsec value or something.

        Returns
        ---------
        out : `telassar.PVSlice` obj
        '''

        if self.world.spatial_unit is None:
            raise ValueError("We need coordinates along the spatial direction")

        if amax is None:
            amax = amin

        if unit is None:
            pmin = max(0, int(amin + 0.5))
            pmax = min(self.shape[0], int(amax + 0.5))

        else:
            pmin = max(0, self.world.offset2pix(amin, nearest=True))
            pmax = min(self.shape[0], self.world.offset2pix(amax, nearest = True) + 1)

        return self[pmin:pmax, :]

    def plot(self, scale = 'linear', ax = None, ax_kws = None, imshow_kws = None,
             vmin = None, vmax = None, zscale = None, emline = None):
        '''
        This function generates an simple plot of the desired data.

        Parameters
        ----------
        scale : str
            the interpolation style desired. default is linear, but can accept
            others from the list:
                ['linear', 'log', 'asinh', 'arcsinh', 'sqrt']
        ax : None or `matplotlib.pyplot.axes` instance
            instanciate plotter with an axis?
        ax_kws : None or dict
            keywords to be passed to the `plt.subplots()` routine
        imshow_kws : None or dict
            keywords to be passed to the `plt.imshow()` routine
        vmin : None or float
            minimum value for plotting normalization
        vmax : None or float
            maximum value for plotting normalization
        zscale : None or str
            do you want a zscale normalization?
        emline : None or str
            can optionally pass an emission line name, and the list of lines
            from above is checked to create a pretty title

        '''
        import matplotlib.pyplot as plt
        from matplotlib.ticker import AutoMinorLocator

        if ax_kws is None:
            ax_kws = {}
        if imshow_kws is None:
            imshow_kws = {}

        emis = None
        if emline is not None:
            if emline in lines.keys():
                emis = lines[emline][2]

                #print(emis)
        if ax is None:
            #fig, ax = plt.subplots(subplot_kw = ax_kws)
            fig, ax = plt.subplots(figsize = (5, 9), **ax_kws)
            #ax = plt.gca()
            #ax.grid(True)

        # set the data and plot parameters
        res = self.copy()
        data = self.data.copy()
        spectral_unit = u.Unit(self.world.spectral_unit).to_string('latex')
        spatial_unit = u.Unit(self.world.spatial_unit).to_string('latex')
        if self.world.wcs.wcs.ctype[0] == 'OFFSET':
            y_type = rf'Offset'
        else:
            y_type = ''
        if self.world.wcs.wcs.ctype[1] == 'VELO':
            x_type = r'V$_{rad}$'
        elif self.world.wcs.wcs.ctype[1] in ['WAVE', 'AWAV']:
            x_type = r'$\lambda$'
        else:
            x_type = ''
        norm = get_plot_norm(data, vmin = vmin, vmax = vmax, zscale = zscale,
                             scale = scale)

        extent = get_plot_extent(self.world)

        ax.format_coord = ImPlotter(res, data)
        cax = ax.imshow(data, interpolation = 'nearest', origin = 'lower', norm =
                        norm, extent = extent,**imshow_kws) #extent = extent,

        if 'title' not in ax_kws.items() and emis is not None:
            ax.set_title(rf'{emis}')
        #    ax.set_title(title)
        ax.set_xlabel(rf'{x_type} ({spectral_unit})')
        ax.set_ylabel(rf'{y_type} ({spatial_unit})')
        ax.margins(0.05)
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())
        ax.tick_params(which = 'major', direction = 'inout', length = 9)
        ax.tick_params(which = 'minor', direction = 'inout', length = 6)

        # format the coordinates
        toggle_unit = True if extent is not None else False
        ax.format_coord = ImPlotter(res, data, toggle_unit)

        return cax

    def plot_contours(self, sig = None, mask = None, levels1 = None, levels2 = None,
                      cmap1 = None, cmap2 = None, cmap3 = None):
        '''
        Generate a contour plot of the data. Useful for jet visualization!

        Parameters
        -----------
        sigma : None or float
            the basis for generating levels. a 3sigma value indicates detection
            of a source, we abbreviate it here to just sigma
        levels1 : None or `np.ndarray` or list
            the contour levels for the jets
        levels2 : None or `np.ndarray` or list
            the contour levels for the background
        cmap1 : None or `matplotlib.colors.Colormap`
            the first colormap to pass to `plt.contour`
        cmap2 : None or `matplotlib.colors.Colormap`
            the second colormap to pass to `plt.contour`
        '''

        import matplotlib.pyplot as plt
        from matplotlib.ticker import AutoMinorLocator
        from astropy.stats import SigmaClip
        from photutils import Background2D, MedianBackground, StdBackgroundRMS

        data = self._data.copy()
        # generate a sigma based on the data?
        if sig is None:
            sigma_clip = SigmaClip(sigma=3)
            mask = self.mask if mask is None else mask
            bkg_estimator = MedianBackground()
            rms_estimator = StdBackgroundRMS()
            bkg = Background2D(data, (60, 30), filter_size = (3,3),
                              sigma_clip=sigma_clip, bkg_estimator=bkg_estimator,
                              bkgrms_estimator = rms_estimator, mask=mask)

        sig = sig if sig is not None else bkg.background_rms_median

        sigsqrt2 = sig * np.sqrt(2)
        if levels1 is None:
            lvls1 = np.array([sig * 2 * np.sqrt(2)**i for i in range(0, 13, 2)])
        if levels2 is None:
            lvls2 = np.linspace(np.log(np.abs(self.min())), 1*sig, 9)
        if cmap1 is None:
            cm1 = 'gist_gray'
        if cmap2 is None:
            cm2 = 'Oranges'
        if cmap3 is None:
            cm3 = 'gray'

        cmap1 = cmap1 if cmap1 is not None else cm1
        cmap2 = cmap2 if cmap2 is not None else cm2
        cmap3 = cmap3 if cmap3 is not None else cm3

        levels1 = levels1 if levels1 is not None else lvls1
        levels2 = levels2 if levels2 is not None else lvls2

        extent = get_plot_extent(self.world)

        spectral_unit = u.Unit(self.world.spectral_unit).to_string('latex')
        spatial_unit = u.Unit(self.world.spatial_unit).to_string('latex')
        if self.world.wcs.wcs.ctype[0] == 'OFFSET':
            y_type = rf'Offset'
        else:
            y_type = ''
        if self.world.wcs.wcs.ctype[1] == 'VELO':
            x_type = r'V$_{rad}$'
        elif self.world.wcs.wcs.ctype[1] in ['WAVE', 'AWAV']:
            x_type = r'$\lambda$'
        else:
            x_type = ''

        fig, ax = plt.subplots(figsize = (4, 9))
        jet1 = ax.contour(data, levels=levels1, cmap=cmap1, extent=extent)
        jet2 = ax.contourf(data, levels=levels1, cmap=cmap2, extent=extent)
        bkgrd = ax.contourf(data, levels=levels2, cmap=cmap3, extent=extent)

        #if 'title' not in ax_kws.items() and emis is not None:
        #    ax.set_title(rf'{emis}')
        #    ax.set_title(title)
        ax.set_xlabel(rf'{x_type} ({spectral_unit})')

        ax.set_ylabel(rf'{y_type} ({spatial_unit})', labelpad = 1)
        ax.margins(0.05)
        ax.xaxis.set_minor_locator(AutoMinorLocator())
        ax.yaxis.set_minor_locator(AutoMinorLocator())
        ax.tick_params(which = 'major', direction = 'inout', length = 9)
        ax.tick_params(which = 'minor', direction = 'inout', length = 6)


        # format the coordinates
        toggle_unit = True if extent is not None else False
        ax.format_coord = ImPlotter(self, data, toggle_unit)
        # make sure the labels aren't clipped?
        fig.tight_layout()
        return ax

    def moments(self, units = False):
        '''
        Return [y_width, x_width] moments (order=1) of a 2D gaussian
        Essentially the same as the example from the SciPy Cookbook:
        https://scipy-cookbook.readthedocs.io/items/FittingData.html

        Parameters
        ----------
        units : bool
            if True, convert the widths to units; otherwise treat them as pixels

        Returns
        ----------
        out : `np.ndarray`
        '''

        # use absolute values to ensure no issues with sqrt
        total = np.abs(data).sum()
        Y, X = np.indices(data.shape)
        y = np.argmax((X * np.abs(data)).sum(axis = 1) / total)
        x = np.argmax((Y * np.abs(data)).sum(axis = 0) /total)
        col = data[int(y), :]
        row = data[:, int(x)]
        xwidth = np.sqrt(np.abs((np.arange(col.size) - y)*col).sum() /
                         np.abs(col).sum())
        ywidth = np.sqrt(np.abs((np.arange(row.size) - x)*row).sum() /
                         np.abs(row).sum())
        height = data.max()
        #mom = np.array([ywidth, xwidth])
        return height, y, x, ywidth, xwidth

    def _prep_data(self, interp = 'no'):
        '''
        any fitting routine will function best when extreme outliers are
        minimised; we may mask values in our view of the data, but `lmfit` will
        operate on the unmasked data. This function will fill the masked values
        with 0 and let `lmfit` work its magic from there

        for now, just leave interp as 'no' because I don't want to work out the
        interpolation, and it will likely not be reliable for extreme outliers
        at the endpoints of the data.

        Parameters
        ----------
        interp : str, 'no', 'linear', or 'spline'
            leaving this as 'no' for now

        Returns
        ---------
        out : np.ndarray
        '''
        #case 'no'
        data = np.ma.filled(self.data, 0.)
        return data

    def prep_model(self, model_list, unit = True):
        """
        Allows for a list of models to be sent to the prepper
        'g' - Guassian Model
        'l' - Lorentzian model
        'v' - Voigt Model

        Using the above, allow the user to quickly enter
        keywords for the model types to save time

        We can add unit support later as well
        """

        # TODO: Add a comprehensive-ish treatment for units
        pix = np.arange(self.shape[0], dtype = np.float64)
        '''if unit is not None:
            # try to convert units: if self.unit isn't angstrom it will fail
            try:
                res = (pix * self.unit).to(unit).value
            except UnitConversionError:
                print("Specified units are not convertible, using pixel values")
                res = pix.copy()
        else:
            unit = self.unit
            res = self.world.pix2val(pix, 0)
        '''

        if unit:
            cunit = u.Unit(self.unit)
        else:
            cunit = u.Unit('pixel')

        xarr = self.world.pix2val(pix) if unit else pix
        res = self._prep_data() #self._data.copy()

        #self.mod_list = model_list
        model_keys = {
                'g' : 'GaussianModel',
                'l' : 'LorentzianModel',
                'v' : 'VoigtModel'
                }

        # Now, set the model_data dict with the data we
        # want to model
        model_data = {
                'x' : xarr,
                'y' : res,
                'unit' : cunit,
                'model' : []
                }

        # Next, make a list where 'type' is key and
        # the model_key values are the values
        mlist = []
        for m in model_list:
            m = m.lower()
            mdict = {}
            mdict['type'] = model_keys[m]
            mlist.append(mdict)
        # update this with the model keyword data
        model_data.update(model = mlist)

        self.model_info = model_data
        return self.model_info


    def generate_model(self, model_list, prepped_model = None, unit = True):

        '''
        Generate a model using a model list and coord data. This function
        utilises `lmfit` to generate the function models, perform a lstsq fit
        to the data, and evaluate the fit for plotting and analysis.
        '''
        # set up the model
        if prepped_model is None:
            prep = self.prep_model(model_list)
        else:
            prep = prepped_model.copy()

        composite_model = None
        params = None
        x = prep['x']
        y = prep['y']
        x_min = x.min()
        x_max = x.max()
        # probably don't need range
        #x_range = x_max - x_min

        # format the coords list as an array, and check if it contains both
        # (x, y) components or just (x, ); if only (x, ) is present evaluate
        # the data at x.
        coords = np.asarray(self.coords)
        if len(coords.shape) == 1:
            if prep['unit'] == 'arcsec':
                k = self.world.val2pix(coords, nearest = True)
            elif prep['unit'] == 'pix':
                k = [int(c + 0.5) for c in coords]
            coords = np.vstack((k, y[k])).T

        #if prep['unit'].to_string() == 'pix':
        #    coords[:, 0] /= 0.2
        # For each basis function in the model dictionary, `lmfit` will need
        # some basic parameters to set the initial conditions. These are
        # estimated by evaluating the data at specified coordinates to set a
        # centroid/offset and peak value, and a basic sigma is provided
        for i, func in enumerate(prep['model']):
            ctr, peak = coords[i]
            prefix = f'm{i}'
            model = getattr(models, func['type'])(prefix=prefix)

            if func['type'] in ['GaussianModel', 'LorentzianModel',
                                'VoigtModel']:
                model.set_param_hint('amplitude', value = 1.1*peak,
                                      min = 0.01 * peak)
                model.set_param_hint('center', value = ctr, min = ctr-10,
                                      max = ctr + 10)
                model.set_param_hint('sigma', min = 1e-6, max = 30)
                default_params = {
                        prefix+'center' : ctr,
                        prefix+'height' : peak,
                        prefix+'sigma' : 5
                    }
            else:
                raise NotImplementedError(f"Model {func['type']} not implemented yet")

            # make the parameters
            model_params = model.make_params(**default_params, **func.get('params', {}))

            if params is None:
                params = model_params
            else:
                params.update(model_params)
            if composite_model is None:
                composite_model = model
            else:
                composite_model = composite_model + model

        return composite_model, params

    def fit_model(self, model_list, coords = None, mode = 'components', plot = False,
                  unit = True):

        """
        Fit a model or composite model based on user specified parameters.
        This function uses `lmfit` to handle the grunt work.

        Parameters
        -----------
        model_list : list, str
            An ordered list of model keywords used to fill the dict with
            the model types.
        coords : list, tuple
            A list of tuples containing (x, y) coordinates for the peaks
            and their locations
        plot : bool
            Do you want the data plotted?
        mode : None, or str
            If plot is True, do you want residuals or components plotted?

        Returns
        ------------
        out : `lmfit.models.results` or whatever it is
        """
        import matplotlib.pyplot as plt
        # if coords are given, format them and override the class attribute
        if coords is not None:
            try:
                coords = np.asarray(coords, dtype = np.float64)
            except ValueError:
                print("Coords must be numeric")
            self.coords = coords

        # make the model
        model_data, params = self.generate_model(model_list)

        result = model_data.fit(self.model_info['y'], params, x = self.model_info['x'])
        self.fit_result = result

        if plot:
            ax = plt.gca()

            # figure out labels for the axes
            if self.unit == 'arcsec':
                xlab = 'Offset (arcsec)'
            if self.unit == 'angstrom':
                xlab = r'$\lambda$'
            else:
                xlab = 'Pixel'

            # Handle motion events?
            def _on_move(event):
                if event.inaxes is not None:
                    xc, yc = event.xdata, event.ydata
                    try:
                        #i = self.world.pix2val(xc)
                        i = self.world.val2pix(xc, nearest = True)
                        x = self.world.pix2val(i)
                        #event.canvas.toolbar.set_message(
                        event.canvas.toolbar.set_message(
                            f'xc = {xc:0.2f} yc = {yc:0.2f} {self.unit} = {x:0.1f} k = {i} data = {self._data[i]:0.2f}' )
                    except Exception:# as e:
                        #print(e) # for debug
                        pass

            # if no mode is given, default to 'components'?
            if mode is None:
                mode = 'components'

            if mode.lower() == 'components':
                ax.scatter(model_data['x'], model_data['y'], s = 4)
                components = result.eval_components(x = model_data['x'])
                for i, model in enumerate(model_data['model']):
                    ax.plot(model_data['x'], components[f'm{i}'], label = f'm{i}_{model["type"]}')
                ax.set_xlabel(xlab)
                # make centroid labels?
                for key, val in result.params.items():
                    if key.endswith('center'):
                        lab = str(np.round(val, 2)) + "''"
                        ax.axvline(val, ls = ':')
                        plt.text(val + 0.2, y = 0.8 * model_data['y'].max(), s = lab,
                                rotation = 90)

            if mode.lower() == 'residuals':
                print('Do something')

    def plot_components(self, **kwargs):
        """
        Make a pretty plot of the components of the fit
        """
        import matplotlib.pyplot as plt

        xarr = self.model_info['x']
        yarr = self.model_info['y']
        res = self.fit_result

        if self.unit is u.Unit('arcsec'):
            xlab = 'Offset (arcsec)'
            #print(xlab)
        elif self.unit is u.Unit('angstrom'):
            xlab = r'$\lambda$'
        else:
            xlab = 'Pixel'


        ax = plt.gca(**kwargs)
        ax.scatter(xarr, yarr, s = 4)
        components = res.eval_components(x = xarr)
        for i, model in enumerate(self.model_info['model']):
            ax.plot(xarr, components[f'm{i}'], label = f'm{i}_{model["type"]}')

        # set labels for the centroids?
        for key, val in res.params.items():
            if key.endswith('center'):
                lab = str(np.round(val, 2)) + "''"
                ax.axvline(val, ls = ':')
                plt.text(val + 0.2, y = 0.8 * self.max(), s = lab,
                        rotation = 90)

        # if ylabel is None:
        #     ylabel = 'ADU'
        # if xlabel is None:
        #     xlabel = xlab
        # ax.set_ylabel(ylabel)
        # ax.set_xlabel(xlabel)


'''
coords = []

# define a function for handling click events
# and saving the coordinates in the list
def _on_click(event):

    global ix, iy

    if event.button == 1:
        ix, iy = event.xdata, event.ydata
        print(f'x = {ix}, y = {iy}')
        coords.append((ix, iy))
    elif event.button == 3:
        fig.canvas.mpl_disconnect(cid)
    return
'''
