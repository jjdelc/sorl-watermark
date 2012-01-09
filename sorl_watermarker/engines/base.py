import os

from django.conf import settings
from sorl.thumbnail.engines.base import EngineBase as ThumbnailEngineBase
from sorl_watermarker.parsers import parse_geometry

# TODO: Put this in it's own package, as done by sorl.thumbnail
STATIC_ROOT = getattr(settings, 'STATIC_ROOT')

THUMBNAIL_WATERMARK = getattr(settings, 'THUMBNAIL_WATERMARK', False)
THUMBNAIL_WATERMARK_ALWAYS = getattr(settings, 'THUMBNAIL_WATERMARK_ALWAYS',
                                     True)
THUMBNAIL_WATERMARK_OPACITY = getattr(settings, 'THUMBNAIL_WATERMARK_OPACITY',
                                      1)
assert 0 <= THUMBNAIL_WATERMARK_OPACITY <= 1 # TODO: raise a ValueError here?

THUMBNAIL_WATERMARK_SIZE = getattr(settings, 'THUMBNAIL_WATERMARK_SIZE', False)
THUMBNAIL_WATERMARK_MIN_APPLICABLE_SIZE = getattr(settings,
    'THUMBNAIL_WATERMARK_MIN_APPLICABLE_SIZE', (0, 0))


class WatermarkEngineBase(ThumbnailEngineBase):
    """
    Extend sorl.thumbnail base engine to support watermarks.

    Rules to apply watermar:
     -  If `no_watermark` is set, don't do anything.
     -  If THUMBNAIL_WATERMARK_ALWAYS, then check if geometry is bigger
        than THUMBNAIL_WATERMARK_MIN_APPLICABLE_SIZE (using typle __gte__)
        and if geometry applies, then apply watermark (if
        THUMBNAIL_WATERMARK_MIN_APPLICABLE_SIZE is not set in settings, it
        will default to (0, 0) so it will always apply.
     -  If THUMBNAIL_WATERMARK_ALWAYS is False, then check if watermark
        options have been manually set on the {% thumbnail %} templatetag
        if so, then apply the watermark with such options.
    """
    def create(self, image, geometry, options):
        image = super(WatermarkEngineBase, self).create(image, geometry,
                                                        options)
        dont_apply = 'no_watermark' in options
        if not dont_apply and (
                (THUMBNAIL_WATERMARK_ALWAYS and
                geometry >= THUMBNAIL_WATERMARK_MIN_APPLICABLE_SIZE) or (
                'watermark'       in options or
                'watermark_pos'   in options or
                'watermark_size'  in options or
                'watermark_alpha' in options)):
            image = self.watermark(image, options)
        return image

    def watermark(self, image, options):
        """
        Wrapper for ``_watermark``

        Takes care of all the options handling.
        """
        if not THUMBNAIL_WATERMARK:
            raise AttributeError('Trying to apply a watermark, '
                                 'however no THUMBNAIL_WATERMARK defined')
        watermark_path = os.path.join(STATIC_ROOT, THUMBNAIL_WATERMARK)

        if not 'watermark_alpha' in options:
            options['watermark_alpha'] = THUMBNAIL_WATERMARK_OPACITY

        if not 'watermark_size' in options and THUMBNAIL_WATERMARK_SIZE:
            options['watermark_size'] = THUMBNAIL_WATERMARK_SIZE
        elif 'watermark_size' in options:
            options['watermark_size'] = parse_geometry(
                                            options['watermark_size'],
                                            self.get_image_ratio(image),
                                        )
        else:
            options['watermark_size'] = False

        return self._watermark(image, watermark_path,
                               options['watermark_alpha'],
                               options['watermark_size'])
