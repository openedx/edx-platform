from __future__ import print_function, division, absolute_import

from doto.logger import log
from doto.connection import connection

import requests


class Domain(object):

    def __str__(self):
        return ("Domain:%s") % (self.id)

    def __repr__(self):
        return ("Domain:%s") % (self.id)

    def __init__(self,conn=None, **kwds):
        self._conn = conn
        self.__dict__.update(kwds)

    def _pprint_table(self, data):
        """
        pprint table: from stackoverflow:
        http://stackoverflow.com/a/8356620
        """

        table = []
        for d in data:
            table.append([unicode(v) for v in d.values()])

        header = d.keys()
        table.insert(0,header)

        col_width = [max(len(x) for x in col) for col in zip(*table)]
        for line in table:
            print("| " + " | ".join("{:{}}".format(x, col_width[i])
                                    for i, x in enumerate(line)) + " |")


    def destroy(self):
        """
        This method allows you to destroy a domain.

        https://api.digitalocean.com/domains/[domain_id]/destroy/?
        client_id=[your_client_id]&api_key=[your_api_key]
        """

        url = "/domains/%s/destroy" % (str(self.id))

        data = self._conn.request(url)

        log.info(data)


    def get_all_records(self,table=False):
        """
        This method returns all of your current domain records.

        https://api.digitalocean.com/domains/[domain_id]/records?
        client_id=[your_client_id]&api_key=[your_api_key]
        """

        log.info("Getting Records")
        url = "/domains/%s/records" % (str(self.id))

        data = self._conn.request(url)

        log.debug(data)

        if table:
            self._pprint_table(data['records'])

        return data['records']

    def get_record(self,record_id=None):
        """
        This method returns the specified domain record.

        :type record_id: int
        :param record_id: ID of record you are trying to retrieve.

        https://api.digitalocean.com/domains/[domain_id]/records/[record_id]?
        client_id=[your_client_id]&api_key=[your_api_key]
        """

        log.info("Getting Record: %d" (record_id))
        url = "/domains/%s/records/%d" % (str(self.id), record_id)

        data = self._conn.request(url)

        log.debug(data)

        return data['record']

    def edit_record(self,record_id=None, record_type=None, data=None,
                         name=None,priority=None,port=None,weight=None,
                         ):
        """
        This method edits an existing domain record.

        :type record_id: int
        :param record_id: ID of record you are trying to retrieve.

        :type record_type: String
        :param record_type: the type of record you would like to create. 'A', 'CNAME', 'NS', 'TXT', 'MX' or 'SRV'.

        :type data: String
        :param data: This is the value of the record.

        :type name: String
        :param name: Required for 'A', 'CNAME', 'TXT' and 'SRV' records otherwise optional

        :type priority: int
        :param priority: required for 'SRV' and 'MX' records otherwise optional

        :type port: int
        :param port: required for 'SRV' records otherwise optional

        :type weight: int
        :param weight: required for 'SRV' records. otherwise optional

        https://api.digitalocean.com/domains/[domain_id]/records/[record_id]/edit?
        client_id=[your_client_id]&api_key=[your_api_key]
        """

        log.info("Editing Record: %d" (record_id))
        url = "/domains/%s/records/%d/edit" % (str(self.id), record_id)

        data = self._conn.request(url,record_type=record_type,
                             data=data,name=name,priority=priority,
                             port=port,weight=weight)

        log.debug(data)

        return data['record']

    def record_destroy(self, record_id=None):
        """
        This method deletes the specified domain record.

        https://api.digitalocean.com/domains/[domain_id]/records/[record_id]/destroy?
        client_id=[your_client_id]&api_key=[your_api_key]
        """

        url = "domains/%s/records/%d/destroy" % (str(self.id),record_id)

        data = self._conn.request(url)

        log.info(data)



