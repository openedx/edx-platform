/*
    Code for editing users and assigning roles within a library context.
*/
// eslint-disable-next-line no-undef
define(['underscore', 'gettext', 'js/views/manage_users_and_roles'],
    function(_, gettext, ManageUsersAndRoles) {
        'use strict';

        // eslint-disable-next-line camelcase
        return function(containerName, users, tplUserURL, current_user_id, allow_actions) {
            function updateMessages(messages) {
                /* eslint-disable-next-line camelcase, no-var */
                var local_messages = _.extend({}, messages);
                // eslint-disable-next-line camelcase
                local_messages.alreadyMember.title = gettext('Already a library team member');
                // eslint-disable-next-line camelcase
                local_messages.deleteUser.messageTpl = gettext(
                    'Are you sure you want to delete {email} from the library “{container}”?'
                );
                // eslint-disable-next-line camelcase
                return local_messages;
            }
            // Roles order are important: first role is considered initial role (the role added to user when (s)he's added
            // Last role is considered an admin role (unrestricted access + ability to manage other users' permissions)
            // Changing roles is performed in promote-demote fashion, so moves only to adjacent roles is allowed
            // eslint-disable-next-line no-var
            var roles = [
                {key: 'library_user', name: gettext('Library User')},
                {key: 'staff', name: gettext('Staff')},
                {key: 'instructor', name: gettext('Admin')}
            ];

            // eslint-disable-next-line no-var
            var options = {
                el: $('#content'),
                containerName: containerName,
                tplUserURL: tplUserURL,
                roles: roles,
                users: users,
                messages_modifier: updateMessages,
                // eslint-disable-next-line camelcase
                current_user_id: current_user_id,
                // eslint-disable-next-line camelcase
                allow_actions: allow_actions
            };

            // eslint-disable-next-line no-var
            var view = new ManageUsersAndRoles(options);
            view.render();
        };
    });
