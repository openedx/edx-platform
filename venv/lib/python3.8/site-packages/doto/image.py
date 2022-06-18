from __future__ import print_function, division, absolute_import

from doto.logger import log

import requests


class Image(object):

    def __str__(self):
        return ("Image:%s") % (self.id)

    def __repr__(self):
        return ("Image:%s") % (self.id)

    def __init__(self, conn=None, **kwds):
        self._conn = conn
        self.__dict__.update(kwds)

    def event_update(self):
        """
        Method to update Image (primarily used to update ip information)

        https://api.digitalocean.com/events/[event_id]/?
        client_id=[your_client_id]&api_key=[your_api_key]
        """

        url = "/events/%s" % (str(self.event_id))
        data = self._conn.request(url)

        log.debug("Updating Event")
        log.debug(data)

        #verbose because droplet_id is unnecessary
        self.event_id = data['event']['id']
        self.percentage = data['event']['percentage']
        self.action_status = data['event']['action_status']
        self.event_type_id = data['event']['event_type_id']



    def percentage_update(self):
        """
        Convenience method to return the percentage of event completion
        """

        self.event_update()
        return self.percentage

    def destroy(self):
        """
        This method allows you to destroy an image.
        There is no way to restore a deleted image so be careful and ensure your data is properly backed up.

        """
        url = "/images/%s/destroy" % (str(self.id))

        data = self._conn.request(url)

        log.debug(data)

    def transfer_image(self, region_id=None):
        """
        This method allows you to transfer an image to a specified region.

        :type image_id: int
        :param image_id: The ID of the image

        :type region_id: int
        :param region_id: The ID of the region to which you would like to transfer.

        """
        # https://api.digitalocean.com/images/[image_id]/transfer/?
        # client_id=[your_client_id]&api_key=[your_api_key]&region_id=[region_id]

        url = "/images/%s/transfer" % (str(self.id))

        data = self._conn.request(url,region_id=region_id)

        self.event_id = data['event_id']

        log.debug(data)
