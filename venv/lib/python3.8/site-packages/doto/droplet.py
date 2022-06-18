from __future__ import print_function, division, absolute_import

from doto.logger import log

import requests
from doto.event import Event


class Droplet(object):

    def __str__(self):
        return ("Droplet:%s") % (self.id)

    def __repr__(self):
        return ("Droplet:%s") % (self.id)

    def __init__(self, conn=None, **kwds):
        self._conn = conn
        self.__dict__.update(kwds)

    def update(self):
        """
        Method to update Droplet (primarily used to update ip information and state changes)

        https://api.digitalocean.com/events/[event_id]/?
        client_id=[your_client_id]&api_key=[your_api_key]
        """

        data = self._conn.request("/droplets/"+str(self.id))

        self.__dict__.update(**data['droplet'])
    
    def event_update(self):
        """
        Method to update Droplet

        https://api.digitalocean.com/events/[event_id]/?
        client_id=[your_client_id]&api_key=[your_api_key]
        """

        url = "/events/%s" % (str(self.event_id))
        data = self._conn.request(url)
        log.debug("Updating Event")
        log.debug(data)

        data['event']['event_id'] = data['event']['id']
        data['event']['id'] = data['event']['droplet_id']

        self.__dict__.update(**data['event'])

    def percentage_update(self):
        """
        Convenience method to return the percentage of event completion

        """

        #needed to grab ip_address
        self.update()

        self.event_update()
        return self.percentage

    def rename(self,name=None):
        """
        This method renames the droplet to the specified name.

        :type name: str
        :param name: Name of the new droplet

        https://api.digitalocean.com/droplets/[droplet_id]/rename/?
        client_id=[your_client_id]&api_key=[your_api_key]&name=[name]
        """


        url = "/droplets/%s/rename" % (str(self.id))

        data = self._conn.request(url,name=name)

        self.event_id = data['event_id']

        log.debug("Renaming: %d To: %s Event: %d" % (self.id, name, self.event_id))
        self.update()

    def rebuild(self, image_id=None, use_current=False):

        """
        This method allows you to reinstall a droplet with a default image.
        This is useful if you want to start again but retain the same IP address for your droplet.

        :type image_id: int
        :param image_id: ID of the image you would like to use to rebuild your droplet with

        :type use_current: BOOL
        :param use_current: Use the current image_id of the droplet during rebuild process

        https://api.digitalocean.com/droplets/[droplet_id]/rebuild/?image_id=[image_id]&
        client_id=[your_client_id]&api_key=[your_api_key]
        """

        if use_current:
            image_id = self.image_id

        url = "/droplets/%s/rebuild" % (str(self.id))

        data = self._conn.request(url,image_id=image_id)

        self.event_id = data['event_id']

        self.update()
        log.debug("Rebuild: %d With: %d Event: %d" % (self.id, image_id, self.event_id))

        return Event(self._conn,self.event_id)
    
    def restore(self, image_id=None):

        """
        This method allows you to restore a droplet with a previous image or snapshot.
        This will be a mirror copy of the image or snapshot to your droplet.
        Be sure you have backed up any necessary information prior to restore.


        :type image_id: int
        :param image_id: ID of the image you would like to use to rebuild your droplet with

        https://api.digitalocean.com/droplets/[droplet_id]/restore/?image_id=[image_id]&
        client_id=[your_client_id]&api_key=[your_api_key]
        """



        url = "/droplets/%s/restore" % (str(self.id))

        data = self._conn.request(url,image_id=image_id)

        self.event_id = data['event_id']

        log.debug("Restoring: %d With: %d Event: %d" % (self.id, image_id, self.event_id))
        self.update()


    def set_backups(self,flag=True):
        """
        This method enables/disables automatic backups
        which run in the background daily to backup your droplet's data.


        :type flag: bool
        :param scrub_data: A bool which enables/disables backups

        https://api.digitalocean.com/droplets/[droplet_id]/enable_backups/?
        client_id=[your_client_id]&api_key=[your_api_key]
        """


        backup_setting = "enable_backups" if flag else "disable_backups"

        url = "/droplets/%s/%s" % (str(self.id), backup_setting)

        data = self._conn.request(url)

        self.event_id = data['event_id']

        log.debug("Destroying: %d, Event: %d" % (self.id, self.event_id))


    def destroy(self, scrub_data=1):
        """
        This method destroys one of your droplets - this is irreversible.

        :type scrub_data: bool
        :param scrub_data: An optional bool which will strictly write 0s to your prior
        partition to ensure that all data is completely erased. True by default

        https://api.digitalocean.com/droplets/[droplet_id]/destroy/?
        client_id=[your_client_id]&api_key=[your_api_key]
        """

        url = "/droplets/%s/destroy" % (str(self.id))

        data = self._conn.request(url,scrub_data=scrub_data)

        self.event_id = data['event_id']

        log.debug("Destroying: %d, Event: %d" % (self.id, self.event_id))

    def reboot(self):
        """
        This method allows you to reboot a droplet.
        This is the preferred method to use if a server is not responding.

        https://api.digitalocean.com/droplets/[droplet_id]/reboot/?
        client_id=[your_client_id]&api_key=[your_api_key]
        """

        url = "/droplets/%s/reboot" % (str(self.id))

        data = self._conn.request(url)

        self.event_id = data['event_id']

        log.debug("Rebooting: %d, Event: %d" % (self.id, self.event_id))

    def shutdown(self):
        """
        This method allows you to shutdown a droplet.
        The droplet will remain in your account.

        https://api.digitalocean.com/droplets/[droplet_id]/shutdown/
        ?client_id=[your_client_id]&api_key=[your_api_key]
        """

        url = "/droplets/%s/shutdown" % (str(self.id))

        data = self._conn.request(url)

        self.event_id = data['event_id']

        log.debug("Shutting Down: %d, Event: %d" % (self.id, self.event_id))
        log.debug("Droplet remains active in your account")



    def power_cycle(self):
        """
        This method allows you to power cycle a droplet.
        This will turn off the droplet and then turn it back on.

        https://api.digitalocean.com/droplets/[droplet_id]/power_cycle/?
        client_id=[your_client_id]&api_key=[your_api_key]
        """

        url = "/droplets/%s/power_cycle" % (str(self.id))

        data = self._conn.request(url)

        self.event_id = data['event_id']

        log.debug("Power Cycle: %d, Event: %d" % (self.id, self.event_id))

    def power_off(self):
        """
        This method allows you to power off a droplet.
        This will turn off the droplet and then turn it back on.

        https://api.digitalocean.com/droplets/[droplet_id]/power_off/?
        client_id=[your_client_id]&api_key=[your_api_key]
        """

        url = "/droplets/%s/power_off" % (str(self.id))

        data = self._conn.request(url)

        self.event_id = data['event_id']

        log.debug("Powering Off: %d, Event: %d" % (self.id, self.event_id))
        
        return Event(self._conn, self.event_id)


    def power_on(self):
        """
        This method allows you to power on a previously powered off droplet.

        https://api.digitalocean.com/droplets/[droplet_id]/power_on/?
        client_id=[your_client_id]&api_key=[your_api_key]
        """

        url = "/droplets/%s/power_on" % (str(self.id))

        data = self._conn.request(url)

        self.event_id = data['event_id']

        log.debug("Powering On: %d, Event: %d" % (self.id, self.event_id))

        return Event(self._conn, self.event_id)

    def password_reset(self):
        """
        This method will reset the root password for a droplet.
        Please be aware that this will reboot the droplet to allow resetting the password.

        https://api.digitalocean.com/droplets/[droplet_id]/password_reset/?
        client_id=[your_client_id]&api_key=[your_api_key]
        """

        url = "/droplets/%s/password_reset" % (str(self.id))

        data = self._conn.request(url)

        self.event_id = data['event_id']

        log.debug("Resetting Password: %d, Event: %d" % (self.id, self.event_id))
        log.debug("Rebooting Droplet")


    def resize(self,size=None):
        """
        This method allows you to resize a specific droplet to a different size.
        This will affect the number of processors and memory allocated to the droplet.

        REQUIRES SNAPSHOT OF DROPLET

        :type size: int
        :param size: The new SIZE id of the droplet


        https://api.digitalocean.com/droplets/[droplet_id]/resize/?size_id=[size_id]&
        client_id=[your_client_id]&api_key=[your_api_key]
        """


        url = "/droplets/%s/resize" % (str(self.id))

        data = self._conn.request(url,size=size)

        self.event_id = data['event_id']

        log.debug("Resizing Droplet: %d, Event: %d" % (self.id, self.event_id))
        log.debug("Rebooting Droplet")

    def create_snapshot(self,name=None):
        """
        This method allows you to take a snapshot of the droplet once it has been powered off,
        which can later be restored or used to create a new droplet from the same image.
        Please be aware this may cause a reboot.

        :type name: string
        :param size: The NAME of the snapshot

        https://api.digitalocean.com/droplets/[droplet_id]/snapshot/?name=[snapshot_name]&
        client_id=[your_client_id]&api_key=[your_api_key]
        """

        url = "/droplets/%s/snapshot" % (str(self.id))

        data = self._conn.request(url,name=name)

        self.event_id = data['event_id']

        log.debug("Taking Snapshot: %d, Event: %d" % (self.id, self.event_id))

        return Event(self._conn, self.event_id)

