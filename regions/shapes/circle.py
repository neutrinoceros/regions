# Licensed under a 3-clause BSD style license - see LICENSE.rst

import math

import numpy as np

from astropy import wcs
from astropy import coordinates
from astropy import units as u

from ..core import PixelRegion, SkyRegion
from ..utils.wcs_helpers import skycoord_to_pixel_scale_angle


class CirclePixelRegion(PixelRegion):
    """
    A circle in pixel coordinates.

    Parameters
    ----------
    center : :class:`~regions.core.pixcoord.PixCoord`
        The position of the center of the circle.
    radius : float
        The radius of the circle
    """

    def __init__(self, center, radius, meta=None, visual=None):
        # TODO: test that center is a 0D PixCoord
        self.center = center
        self.radius = radius
        self.meta = meta or {}
        self.visual = visual or {}

    @property
    def area(self):
        return math.pi * self.radius ** 2

    def __contains__(self, pixcoord):
        return np.hypot(pixcoord.x - self.center.x,
                        pixcoord.y - self.center.y) < self.radius

    def to_shapely(self):
        return self.center.to_shapely().buffer(self.radius)

    def to_sky(self, mywcs, mode='local', tolerance=None):
        # TOOD: needs to be implemented
        raise NotImplementedError("")

    def to_mask(self, mode='center'):
        # TOOD: needs to be implemented
        raise NotImplementedError("")

    def to_mpl_patch(self, **kwargs):
        """Convert to mpl patch.

        Returns
        -------
        patch : `~matplotlib.mpatches.Circle`
            Matplotlib patch
        """
        import matplotlib.patches as mpatches

        patch = mpatches.Circle(self.center, self.radius, **kwargs)
        return patch


class CircleSkyRegion(SkyRegion):
    """
    A circle in sky coordinates.

    Parameters
    ----------
    center : :class:`~astropy.coordinates.SkyCoord`
        The position of the center of the circle.
    radius : :class:`~astropy.units.Quantity`
        The radius of the circle in angular units
    """

    def __init__(self, center, radius, meta=None, visual=None):
        # TODO: test that center is a 0D SkyCoord
        self.center = center
        self.radius = radius
        self.meta = meta or {}
        self.visual = visual or {}

    @property
    def area(self):
        return math.pi * self.radius ** 2

    def __contains__(self, skycoord):
        return self.center.separation(skycoord)

    def to_pixel(self, mywcs, mode='local', tolerance=None):
        """
        Given a WCS, convert the circle to a best-approximation circle in pixel
        dimensions.

        Parameters
        ----------
        mywcs : `~astropy.wcs.WCS`
            A world coordinate system
        mode : 'local' or not
            not implemented
        tolerance : None
            not implemented

        Returns
        -------
        CirclePixelRegion
        """

        if mode != 'local':
            raise NotImplementedError()
        if tolerance is not None:
            raise NotImplementedError()

        wcsframe = wcs.utils._wcs_to_celestial_frame_builtin(mywcs)
        center_in_wcsframe = self.center.transform_to(wcsframe)

        xpix, ypix = mywcs.wcs_world2pix(center_in_wcsframe.spherical.lon,
                                         center_in_wcsframe.spherical.lat, 0)

        if self.radius.unit.physical_type == 'angle':
            central_pos = coordinates.SkyCoord([mywcs.celestialwcs.crval],
                                               frame=self.center.name,
                                               unit=wcs.wcs.cunit)
            xc, yc, scale, angle = skycoord_to_pixel_scale_angle(central_pos,
                                                                 wcs)
            radius_pix = (scale * self.radius).to(u.pixel).value
        else:  # pixel: this should not be possible.
            radius_pix = self.radius.value

        pixel_positions = np.array([xc, yc]).transpose()

        return CirclePixelRegion(pixel_positions, radius_pix)

    def to_mpl_patch(self, ax, **kwargs):
        """Convert to mpl patch using a given wcs axis

        Parameters
        ----------
        ax : `~astropy.wcsaxes.WCSAxes`
            WCS axis object
        kwargs : dict
            kwargs are forwarded to mpatches.Circle

        Returns
        -------
        patch : `~matplotlib.mpatches.Circle`
            Matplotlib patch
        """

        import matplotlib.patches as mpatches

        val = self.center.icrs
        center = (val.ra.to('deg').value, val.dec.to('deg').value)

        temp = dict(transform=ax.get_transform('icrs'),
                    radius=self.radius.to('deg').value)
        kwargs.update(temp)
        for key, value in self.visual.items():
            kwargs.setdefault(key, value)
        patch = mpatches.Circle(center, **kwargs)

        return patch