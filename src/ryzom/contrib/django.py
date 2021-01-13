from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage


class Static:
    '''Return a static url for an app asset.

    :param str src: The app path of the asset.
    '''
    def __init__(self, src):
        self._data = src
        self.url = staticfiles_storage.url(src)

    def __str__(self):
        return self.url
