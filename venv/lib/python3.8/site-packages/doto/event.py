'''
Created on Mar 25, 2014

@author: sean
'''
import time

class Event(object):
    
    EVENT_TYPES = {
                   17: 'restore',
                   18: 'power_on',
                   19: 'power_off',
                   }
    
    def __init__(self, conn, event_id):
        self.conn = conn
        self.event_id = event_id
        self._data = None
    
    
    def __repr__(self):
        data = self.data
        
        event_type = self.EVENT_TYPES.get(data['event_type_id'], data['event_type_id'])
        return '<Event id=%s type=%s status=%s>' % (data['id'], event_type, data.get('action_status'))
    
    def refresh(self):
        res = self.conn.request('/events/%s' % self.event_id)
        self._data = res['event']
    
    @property
    def data(self):
        if self._data is None:
            self.refresh()
        return self._data
    
    @property
    def status(self):
        return self.data.get('action_status')
    
    def wait(self, status='done', timeout=60 * 60 * 10, poll_interval=5, callback=None):
        start = time.time()
        while 1:
            self.refresh()
            if time.time() > start + timeout:
                raise Exception("timeout waiting for status")
            if self.status == status:
                return
            if callback: callback(status, self)
            time.sleep(poll_interval)
    