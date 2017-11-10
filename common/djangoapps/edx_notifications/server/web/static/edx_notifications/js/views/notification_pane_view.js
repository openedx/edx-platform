var NotificationPaneView = Backbone.View.extend({
    initialize: function(options){
        this.global_variables = options.global_variables;
        this.view_templates = options.view_templates;
        this.counter_icon_view = options.counter_icon_view;
        this.namespace = options.namespace;
        this.endpoints = options.endpoints;

        var self = this;

        /* get out main underscore view template */
        this.template = _.template($('#xns-pane-template').html());

        // set up our URLs for the API
        this.unread_msgs_endpoint = options.endpoints.user_notifications_unread_only;
        this.all_msgs_endpoint = options.endpoints.user_notifications_all;
        this.mark_all_read_endpoint = options.endpoints.mark_all_user_notifications_read;
        this.mark_notification_read_endpoint = options.endpoints.user_notification_mark_read;

        this.renderer_templates_url_endpoint = options.endpoints.renderer_templates_urls;

        /* query endpoints to get a list of all renderer template URLS */
        $.get(this.renderer_templates_url_endpoint).done(function(data){
            self.process_renderer_templates_urls(data);
        });

        // apply namespacing - if set - to our Ajax calls
        if (this.namespace) {
            this.unread_msgs_endpoint = this.append_url_param(this.unread_msgs_endpoint, 'namespace', this.namespace);
            this.all_msgs_endpoint = this.append_url_param(this.all_msgs_endpoint, 'namespace', this.namespace);
        }

        /* set up our collection */
        this.collection = new UserNotificationCollection();

        /* set the API endpoint that was passed into our initializer */
        this.collection.url = this.unread_msgs_endpoint;

        /* re-render if the model changes */
        this.listenTo(this.collection, 'change', this.collectionChanged);

        this.hydrate();
    },

    append_url_param: function(baseUrl, key, value) {
      key = encodeURI(key); value = encodeURIComponent(value);
      var path = baseUrl.split('?')[0];
      var kvp = baseUrl.split('?')[1].split('&');
      var i=kvp.length; var x; while(i--)
      {
          x = kvp[i].split('=');
          if (x[0]==key)
          {
              x[1] = value;
              kvp[i] = x.join('=');
              break;
          }
      }
      if(i<0) {kvp[kvp.length] = [key,value].join('=');}
      return path + '?' + kvp.join('&');
    },

    events: {
        'click .xns-all-action': 'allUserNotificationsClicked',
        'click .xns-unread-action': 'unreadNotificationsClicked',
        'click .xns-mark-read-action': 'markNotificationsRead',
        'click .xns-notification-preferences': 'notificationPreferencesView',
        'click .xns-hide-pane': 'hidePane',
        'click .xns-item': 'visitNotification',
        'click .xns-close-item': 'closeNotification',
        'click .xns-content': 'preventHidingWhenClickedInside'
    },

    template: null,

    selected_pane: 'unread',

    process_renderer_templates_urls: function(data) {
        /*
        This will go through all Underscore Notification Renderer Templates
        that have been registered with the system and load them
        */
        var self = this;

        var number_to_fetch = 0;
        for (var item in data) {
            if (data.hasOwnProperty(item)) {
                number_to_fetch++;
            }
        }

        var renderer_templates = {};

        _.each(data, function(url, renderer_class) {
            $.ajax({url: url, dataType: "html", context: renderer_class})
            .error(function(jqXHR, textStatus, errorThrown){
                console.error('Could not load template ' + renderer_class + ' at ' + url);
                number_to_fetch--;
            })
            .done(function(template_data) {
                renderer_templates[renderer_class] = _.template(template_data);
                number_to_fetch--;
                if (number_to_fetch === 0) {
                    self.renderer_templates = renderer_templates;
                    self.render();
                }
            });
        });
    },

    hydrate: function() {
        /* This function will load the bound collection */

        /* add and remove a class when we do the initial loading */
        /* we might - at some point - add a visual element to the */
        /* loading, like a spinner */
        var self = this;
        self.$el.addClass('xns-ui-loading');
        this.collection.fetch({
            success: function(){
                self.$el.removeClass('xns-ui-loading');
                self.render();
            }
        });
    },

    /* all notification renderer templates */
    renderer_templates: {},

    collectionChanged: function() {
        /* redraw for now */
        this.render();
    },

    render: function() {
        /* if we have data in our collection AND we have loaded */
        /* all of the Notification renderer templates, then let's */
        /* enumerate through all of the notifications we have */
        /* and render each one */

        var grouped_user_notifications = [];

        if (this.selected_pane == 'unread') {
            notification_group_renderings = this.render_notifications_by_type();
        } else {
            notification_group_renderings = this.render_notifications_by_day();
        }

        var always_show_dates_on_unread = (typeof this.global_variables.always_show_dates_on_unread !== undefined && this.global_variables.always_show_dates_on_unread);

        /* now render template with our model */
        var _html = this.template({
            global_variables: this.global_variables,
            grouped_user_notifications: notification_group_renderings,
            selected_pane: this.selected_pane,
            always_show_dates_on_unread: always_show_dates_on_unread
        });

        this.$el.html(_html);

        // make sure the right tab is highlighted
        this.$el.find($('ul.xns-tab-list > li')).removeClass('active');
        var class_to_activate = (this.selected_pane == 'unread') ? 'xns-unread-action' : 'xns-all-action';
        this.$el.find('.'+class_to_activate).addClass('active');

        // apply some logic with regards to enabling/disabling the 'Mark as read'
        // action link. We should only enable this if we are on the 'unread' pane
        // and we have at least 1 unread notificatons
        if (this.selected_pane == 'unread' && this.collection.length > 0) {
            $('.xns-mark-read-action').removeClass('disabled');
        } else {
            $('.xns-mark-read-action').addClass('disabled');
        }
    },
    /* this describes how we want to group together notification types into visual groups */
    grouping_config: {
        /* this will ultimately be served up by the server */
        groups: {
            'announcements': {
                name: 'announcements',
                display_name: 'Announcements',
                group_order: 1
            },
            'group_work': {
                name: 'group_work',
                display_name: 'Group Work',
                group_order: 2
            },
            'leaderboards': {
                name: 'leaderboards',
                display_name: 'Leaderboards',
                group_order: 3
            },
            'discussions': {
                name: 'discussions',
                display_name: 'Discussion',
                group_order: 4
            },
            '_default': {
                name: '_default',
                display_name: 'Other',
                group_order: 5
            }
        },
        type_mapping: {
            'open-edx.lms.discussions.cohorted-thread-added': 'group_work',
            'open-edx.lms.discussions.cohorted-comment-added': 'group_work',
            'open-edx.lms.discussions.*': 'discussions',
            'open-edx.lms.leaderboard.*': 'leaderboards',
            'open-edx.studio.announcements.*': 'announcements',
            'open-edx.xblock.group-project.*': 'group_work',
            'open-edx.xblock.group-project-v2.*': 'group_work',
            '*': '_default'
        }
    },
    get_group_name_for_msg_type: function(msg_type) {
        /* see if there is an exact match */
        if (msg_type in this.grouping_config.type_mapping) {
            var group_name = this.grouping_config.type_mapping[msg_type];
            if (group_name in this.grouping_config.groups) {
                return group_name;
            }
        }

        /* no exact match so lets look upwards for wildcards */
        var search_type = msg_type;
        var dot_index = search_type.lastIndexOf('.');
        while (dot_index != -1 && search_type != '*') {
            search_type = search_type.substring(0, dot_index);

            var key = search_type + '.*';

            if (key in this.grouping_config.type_mapping) {
                var group_name = this.grouping_config.type_mapping[key];
                if (group_name in this.grouping_config.groups) {
                    return group_name;
                }
            }
            dot_index = search_type.lastIndexOf('.');
        }

        /* look for global wildcard */
        if ('*' in this.grouping_config.type_mapping) {
            var key = '*';
            var group_name = this.grouping_config.type_mapping[key];
            if (group_name in this.grouping_config.groups) {
                return group_name;
            }
        }

        /* this really shouldn't happen. This means misconfiguration */
        return null;
    },
    render_notifications_by_type: function() {
        var user_msgs = this.collection.toJSON();
        var grouped_data = {};
        var notification_groups = [];
        var group_orderings = null;
        var self = this;

        // use Underscores built in group by function
        grouped_data = _.groupBy(
            user_msgs,
            function(user_msg) {
                // group together according to the group rules in grouping_config
                return self.get_group_name_for_msg_type(user_msg.msg.msg_type.name);
            }
        );

        // then we want to order the groups according to the grouping_config
        // so we can specify which groups go up at the top
        group_orderings = _.sortBy(
            this.grouping_config.groups,
            function(group) {
                return group.group_order;
            }
        );

        // Now iterate over the groups and perform
        // a sort by date (desc) inside each msg inside the group and also
        // create a rendering of each message
        _.each(group_orderings, function(group_ordering) {
            var group_key = group_ordering.name;
            if (group_key in grouped_data) {
                notification_groups.push({
                    // pull the header name from the grouping_config
                    group_title: self.grouping_config.groups[group_key].display_name,
                    messages: self.get_group_rendering(grouped_data[group_key])
                });
            }
        });

        return notification_groups;
    },
    render_notifications_by_day: function() {
        var user_msgs = this.collection.toJSON();
        var grouped_data = {};
        var notification_groups = [];
        var group_orderings = null;
        var self = this;

        // group by create date
        grouped_data = _.groupBy(
            user_msgs,
            function(user_msg) {
                var date = user_msg.created;
                // remove the time of day portion of our create time
                // to group things by day
                // NOTE what about timezone changes? We
                // could clean things up post hydation?
                return new Date(date).clearTime();
            }
        );

        // now compute orderings
        group_orderings = [];
        for (var key in grouped_data) {
            group_orderings.push(key);
        }

        // Now iterate over the groups and perform
        // a sort by date (desc) inside each msg inside the group and also
        // create a rendering of each message
        _.each(group_orderings, function(group_key) {
            if (group_key in grouped_data) {
                var group_data = grouped_data[group_key];

                // on the by date grouping, also inject the 'type group' information
                // on every notification
                _.each(group_data, function(item){
                    item.group_name = self.get_group_name_for_msg_type(item.msg.msg_type.name);
                });
                notification_groups.push({
                    // pull the header name from the first time in the group
                    // since they are all on the same day
                    group_title: new Date(group_data[0].created).toString('MMM dd, yyyy'),
                    messages: self.get_group_rendering(group_data)
                });
            }
        });

        return notification_groups;
    },
    get_group_rendering: function(group_data) {

        var renderings = [];

        // Then within each group we want to sort
        // by create date, descending, so call reverse()
        var sorted_data = _.sortBy(
            group_data,
            function(user_msg) {
                return user_msg.created;
            }
        ).reverse();

        // Loop through each msg in the current group
        // and create a rendering of it
        for (var j = 0; j < sorted_data.length; j++) {
            var user_msg = sorted_data[j];
            var msg = user_msg.msg;
            var renderer_class_name = msg.msg_type.renderer;

            // check to make sure we have the Underscore rendering
            // template loaded, if not, then skip it.
            var render_context = jQuery.extend(true, {}, msg.payload);

            // pass in the selected_view in case the
            // Underscore templates will how different
            // renderings depending on which tab is selected
            render_context['__view'] = this.selected_pane;

            // also pass in the date the notification was created
            render_context['__created'] = user_msg.created;

            // also do a conversaion of the create date to a friendly
            // display string

            var created_str = '';
            var created_date = new Date(user_msg.created);
            if (Date.equals(new Date(created_date).clearTime(), Date.today())) {
                created_str = 'Today at '+ created_date.toString("h:mmtt");
            } else {
                created_str = created_date.toString("MMMM dd, yyyy") + ' at ' + created_date.toString("h:mmtt");
            }
            render_context['__display_created'] = created_str;

            if (renderer_class_name in this.renderer_templates) {
                try {
                    if (renderer_class_name in this.renderer_templates) {
                        var notification_html = this.renderer_templates[renderer_class_name](render_context);

                        renderings.push({
                            user_msg: user_msg,
                            msg: msg,
                            /* render the particular NotificationMessage */
                            html: notification_html,
                            group_name: this.get_group_name_for_msg_type(msg.msg_type.name)
                        });
                    } else {
                        console.error('Renderer template ' + renderer_class_name + ' not loaded. Skipping rendering message...');
                    }
                } catch(err) {
                    console.error('Could not render Notification type ' + msg.msg_type.name + ' with template ' + renderer_class_name + '. Error: "' + err + '". Skipping....')
                }
            }
        }

        return renderings;
    },
    allUserNotificationsClicked: function(e) {
        // check if the event.currentTarget class has already been active or not
        if (this.selected_pane != 'all') {
            /* set the API endpoint that was passed into our initializer */
            this.collection.url = this.all_msgs_endpoint;
            this.selected_pane = 'all';
            this.hydrate();
        }
        e.preventDefault();
    },
    unreadNotificationsClicked: function(e) {
        // check if the event.currentTarget class has already been active or not
        /* set the API endpoint that was passed into our initializer */
        this.collection.url = this.unread_msgs_endpoint;
        this.selected_pane = 'unread';
        this.hydrate();
        if (e !== null) {
            e.preventDefault();
        }
    },
    markNotificationsRead: function(e) {
        // this is only supported on the 'unread' view
        if (this.selected_pane == 'unread' &&
            (this.collection.url !== this.mark_all_read_endpoint || this.collection.length > 0)) {
            // set the API endpoint that was passed into our initializer
            this.collection.url = this.mark_all_read_endpoint;

            // make the async call to the backend REST API
            // after it loads, the listenTo event will file and
            // will call into the rendering
            var self = this;
            self.$el.addClass('xns-ui-loading');
            var data = {};
            if (this.namespace) {
                data = {
                    namespace: this.namespace
                };
            }
            self.collection.fetch(
                {
                    headers: {
                        "X-CSRFToken": this.getCSRFToken()
                    },
                    type: 'POST',
                    data: data,
                    success: function () {
                        self.$el.removeClass('xns-ui-loading');
                        self.selected_pane = 'unread';
                        self.render();

                        // fetch the latest notification count
                        self.counter_icon_view.refresh();
                    }
                }
            );
        }
        e.preventDefault();
    },
    getCSRFToken: function() {
        var cookieValue = null;
        var name='csrftoken';
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    },
    visitNotification: function(e) {
        var messageId = $(e.currentTarget).find('span').data('msg-id');
        var clickLink = $(e.currentTarget).find('span').data('click-link');

        if (this.selected_pane === "unread") {
            this.collection.url = this.mark_notification_read_endpoint + messageId;

            var self = this;
            self.collection.fetch(
                {
                    headers: {
                        "X-CSRFToken": this.getCSRFToken()
                    },
                    data: {
                      "mark_as": "read"
                    },
                    type: 'POST',
                    success: function () {
                        if (clickLink) {
                            window.location.href = clickLink;
                        } else {
                            self.unreadNotificationsClicked(e);
                            // fetch the latest notification count
                            self.counter_icon_view.refresh();
                        }
                    }
                }
            );
        } else if (clickLink){
            window.location.href = clickLink;
        }
    },
    closeNotification: function(e) {
        var messageId = $(e.currentTarget).data('msg-id');

        if (this.selected_pane === "unread") {
            this.collection.url = this.mark_notification_read_endpoint + messageId;

            var self = this;
            self.collection.fetch(
                {
                    headers: {
                        "X-CSRFToken": this.getCSRFToken()
                    },
                    data: {
                      "mark_as": "read"
                    },
                    type: 'POST',
                    success: function () {
                        if ($(".xns-items li").length > 1) {
                            if(!($('#'+messageId).next().is( "li" )) && $('#'+messageId).prev().is( "h3" )){
                                $('#'+messageId).prev().remove();
                            }
                            $('#'+messageId).remove();
                            self.counter_icon_view.refresh();
                        }
                        else {
                            self.unreadNotificationsClicked(e);
                            // fetch the latest notification count
                            self.counter_icon_view.refresh();
                        }
                    }
                }
            );
            e.preventDefault();
            e.stopPropagation();
        }
    },
    hidePane: function() {
        this.$el.hide();
    },
    showPane: function() {
        // when showing pane
        // always have the 'unread' view selected
        if (this.selected_pane != 'unread') {
            this.collection.reset();
            // clear out any previously rendered html
            this.$el.html('');
            this.unreadNotificationsClicked(null);
        }
        this.$el.show();
    },
    preventHidingWhenClickedInside: function(e) {
      e.stopPropagation();
    },
    isVisible: function() {
      if ($('.xns-container').is(':visible')) {
        return true;
      }
      else {
        return false;
      }
    },
    /* cached notifications preferences tab view */
    notification_preferences_tab: null,

    notificationPreferencesView: function(e){
        // make sure the right tab is highlighted
        this.$el.find($('ul.xns-tab-list > li')).removeClass('active');
        $(e.currentTarget).addClass('active');
        if (this.selected_pane != 'notification_preference') {
            this.selected_pane = 'notification_preference';
            $('.xns-mark-read-action').addClass('disabled');

            if (!this.notification_preferences_tab) {
                this.notification_preferences_tab = new NotificationPreferencesView({
                    el: this.$el.find('.xns-list-body'),
                    endpoints: this.endpoints,
                    global_variables: this.global_variables
                });
            }
            else {
                // redraw the settings notification_preferences_tab.
                this.notification_preferences_tab.showFetchedPreferences(this.$el.find('.xns-list-body'));
            }
        }
        e.preventDefault();
    }
});
