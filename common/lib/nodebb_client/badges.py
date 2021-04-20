"""
Sync badges with pynodebb
"""
from pynodebb.api import Resource


class ForumBadge(Resource):
    """
    Added custom methods to the default Resources class of pynodebb package
    """

    def save(self, badge_info):
        """
        save badge configuration
        """
        payload = badge_info
        # TODO: We need to define CONSTANTS for api urls instead hadrcoding them everywhere.
        return self.client.post('/api/v2/badge-config/{}'.format(badge_info['id']), **payload)

    def delete(self, badge_id):
        """
        delete badge configuration
        """
        return self.client.delete('/api/v2/badge-config/{}'.format(badge_id))

    def get_progress(self, request_data):
        """
        Get badges progress
        """
        payload = request_data
        return self.client.post('/api/v2/badges/badge-progress', **payload)
