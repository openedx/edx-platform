from pynodebb.api.groups import Group


class ForumGroup(Group):
    """
    Added custom methods to the default Group class of pynodebb package
    """

    def create(self, **kwargs):
        """
        Create a group on NodeBB

        URL: /api/v2/groupChat/create
        METHOD: POST
        BODY : {
            "team":["User3","User4"], (mandatory)
            "roomName": "6th group",
            "teamDescription": "",(mandatory)
            "teamLanguage": "",
            "teamCountry": "",
            "discussionTitle": "",
            "discussionDescription": "",
            "courseName": "" (mandatory)
        }

        RESPONSE: {
            "message": "room successfully created",
            "url": "/chats/25",
            "room": "25"
        }
        """
        return self.client.post('/api/v2/groupChat/create', **kwargs)

    def update(self, room_id, **kwargs):
        """
        Update a group on NodeBB

        URL: /api/v2/groupChat/update/:roomId
        METHOD: PUT
        BODY: {
            "team":["User3","User4", "User2"],
            "roomName": "fourth",
            "teamDescription": "",
            "teamLanguage": "",
            "teamCountry": "",
            "discussionTitle": "",
            "discussionDescription": "",
            "courseName": ""
        }


        RESPONSE: {
            "message": "successfully updated ",
            "url": "/chats/24",
            "room": "24"
        }
        """
        return self.client.put('/api/v2/groupChat/update/%s' % room_id, **kwargs)

    def delete(self, room_id, **kwargs):
        """
        Delete a group from Nodebb

        DELETE:
        METHOD: DELETE
        URL: /groupChat/:ownerUserName/delete/:roomId

        BODY: {
            "team":["User4"]
        }

        RESPONSE: {
            "message": "successfully deleted ",
            "url": "/chats/25",
            "room": "25"
        }

        NOTE: please send all user name in delete api for deleting the whole team.
        """
        return self.client.delete('/api/v2/groupChat/delete/%s' % room_id, **kwargs)
