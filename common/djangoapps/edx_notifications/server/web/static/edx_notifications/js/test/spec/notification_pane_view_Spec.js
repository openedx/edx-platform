describe("NotificationPaneView", function(){

    beforeEach(function(){
        this.server = sinon.fakeServer.create();
        setFixtures(
            '<div>' +
            '<img class="xns-icon" src="/static/edx_notifications/img/notification_icon.jpg" />' +
            '<span class="xns-counter"></span>' +
            '</div>' +
            '<div class="xns-pane">' +
            '<script type="text/template" id="xns-pane-template">' +
            '<div class="xns-container">' +
            '<div class="xns-content <%= selected_pane %>">' +
            '<div class="xns-list-header">' +
               '<h2>Notifications</h2>' +
                '<div class="xns-actions">' +
                    '<ul class="xns-tab-list">' +
                        '<li class="xns-unread-action active"><a  href="#">View unread</a></li>' +
                        '<li class="xns-all-action"><a href="#">View all</a></li>' +
                        '<li class="xns-mark-read-action"><a href="#">Mark as read</a></li>' +
                        '<% if (typeof this.global_variables.hide_link_is_visible != "undefined" &&' +
                        'this.global_variables.hide_link_is_visible != "False") { %>' +
                            '<li class="xns-hide-pane"><a href="#">Hide</a></li>' +
                        '<% } %>' +
                    '</ul>' +
                '</div>' +
            '</div>' +
            '<div class="xns-list-body">' +
                '<ul class="xns-items">' +
                    '<% if (typeof grouped_user_notifications == "undefined" || grouped_user_notifications.length == 0) { %>' +
                       ' <li class="xns-empty-list">' +
                            '<p class="xns-no-notifications-msg xns-item">You have no unread notifications.</p>' +
                        '</li>' +
                    '<% } else { %>' +
                        '<% _.each(grouped_user_notifications, function(grouped_user_notification){ %>' +
                            '<h3 class="borderB padB5 uppercase bold marB10 xns-group"><%= grouped_user_notification.group_title %></h3>' +
                            '<% _.each(grouped_user_notification.messages, function(message){ %>' +
                                '<li class="marB10 padB5 borderB xns-item">' +
                                    '<% if (selected_pane == "unread" && always_show_dates_on_unread) { %>' +
                                        '<div class="xns-date">' +
                                            '<% if (Date.equals(new Date(message.msg.created).clearTime(), Date.today())) { %>' +
                                                'Today at <%= new Date(message.msg.created).toString("h:mmtt") %>' +
                                            '<%} else {%>' +
                                                '<%= new Date(message.msg.created).toString("MMMM dd, yyyy") %> at <%= new Date(message.msg.created).toString("h:mmtt") %>' +
                                            '<% } %>' +
                                        '</div>' +
                                    '<% } %>' +
                                    '<div class="xns-body">' +
                                        '<span data-msg-id="<%= message.msg.id %>" data-click-link="<%=message.msg.payload["_click_link"]%>" class="xns-<%= message.group_name %>"><%= message.html %></span>' +
                                    '</div>' +
                                '</li>' +
                            '<% }); %>' +
                        '<% }); %>' +
                    '<% } %>' +
                '</ul>' +
            '</div>' +
        '</div>' +
    '</div>' +
'</script>' +
'</div>'
        );
        this.notification_pane = new NotificationPaneView({
            el: $(".xns-icon"),
            count_el: $(".xns-counter"),
            pane_el: $(".xns-pane"),
            endpoints: {
                unread_notification_count: "/unread/count/?read=False&unread=True",
                mark_all_user_notifications_read: "/mark/as/read",
                user_notifications_all:"/all/notifications/?read=True&unread=True",
                user_notifications_unread_only: "unread/notifications/?read=False&unread=True",
                renderer_templates_urls: "/renderer/templates",
                user_notification_mark_read: "read/notifications"
            },
            global_variables: {
                app_name: "none"
            },
            view_templates: "/view/templates"
        });
        this.notification_pane.render();
        this.all_notifications_target = $(".xns-all-action");
        this.unread_notifications_target = $(".xns-unread-action");
        this.mark_notifications_read_target = $(".xns-mark-read-action");
        this.notification_content_target = $(".xns-items .xns-item");
        this.hide_pane_target = $(".xns-hide-pane");
        this.prevent_click_target = $(".xns-content");
        this.empty_list_target = $(".xns-no-notifications-msg");
    });

    afterEach(function() {
        this.server.restore();
    });

    it("checks if template function is defined", function(){
        expect(this.notification_pane.template).toBeDefined();
    });

    it("successfully sets view templates url", function(){
        expect(this.notification_pane.view_templates).toBe('/view/templates');
    });

    it("successfully sets given urls in endpoint", function(){
        expect(this.notification_pane.mark_all_read_endpoint).toEqual('/mark/as/read');
        expect(this.notification_pane.all_msgs_endpoint).toBe('/all/notifications/?read=True&unread=True');
        expect(this.notification_pane.unread_msgs_endpoint).toBe('unread/notifications/?read=False&unread=True');
        expect(this.notification_pane.renderer_templates_url_endpoint).toEqual('/renderer/templates');
    });

    it("successfully sets url with namespaces in endpoint if name space is provided", function(){
        this.protoView = new NotificationPaneView({
            el: $(".xns-icon"),
            count_el: $(".xns-counter"),
            pane_el: $(".xns-pane"),
            endpoints: {
                unread_notification_count: "/unread/count/?read=False&unread=True",
                user_notifications_all:"/all/notifications/?read=True&unread=True",
                user_notifications_unread_only: "unread/notifications/?read=False&unread=True"
            },
            namespace: "foo",
            global_variables: {
                app_name: "none"
            }

        });
        this.protoView.render();
        expect(this.protoView.all_msgs_endpoint).toBe('/all/notifications/?read=True&unread=True&namespace=foo');
        expect(this.protoView.unread_msgs_endpoint).toBe('unread/notifications/?read=False&unread=True&namespace=foo');
    });

    it("initializes collection_url with unread notification endpoints as default value", function(){
        expect(this.notification_pane.collection.url).toEqual('unread/notifications/?read=False&unread=True');
    });

    it("initializes selected pane with unread notification as default value", function(){
        expect(this.notification_pane.selected_pane).toEqual('unread');
    });

    it("verifies that render_notification_by_type is called if selected pane is unread", function() {
        renderSpy = spyOn(this.notification_pane, 'render_notifications_by_type');
        this.notification_pane.render();
        expect(renderSpy).toHaveBeenCalled()
    });

    it("initializes .xns-content htm", function(){
        expect(this.empty_list_target.html()).toContain('You have no unread notifications');
    });

    it("calls allUserNotificationsClicked function on clicking .user_notifications_all", function(){
        spyOn(this.notification_pane, 'allUserNotificationsClicked');
        this.notification_pane.delegateEvents();
        this.all_notifications_target.click();
        expect(this.notification_pane.allUserNotificationsClicked).toHaveBeenCalled();
    });

    it("sets collection url new value after calling allUserNotificationsClicked function", function(){
        this.all_notifications_target.click();
        expect(this.notification_pane.collection.url).toContain('/all/notifications');
    });

    it("sets selected pane new value after calling allUserNotificationsClicked function", function(){
        this.all_notifications_target.click();
        expect(this.notification_pane.selected_pane).toContain('all');
    });

    it("calls unreadNotificationsClicked function on clicking .unread_notifications", function(){
        var unreadNotificationsSpy = spyOn(this.notification_pane, 'unreadNotificationsClicked');
        this.notification_pane.delegateEvents();
        this.unread_notifications_target.click();
        expect(unreadNotificationsSpy).toHaveBeenCalled();
    });

    it("sets collection url new value after calling unreadNotificationsClicked function", function(){
        this.unread_notifications_target.click();
        expect(this.notification_pane.collection.url).toContain('unread/notifications/?read=False&unread=True');
    });

    it("sets selected pane new value after calling unreadNotificationsClicked function", function(){
        this.unread_notifications_target.click();
        expect(this.notification_pane.selected_pane).toContain('unread');
    });

    it("calls markNotificationsRead function on clicking .mark_notifications_read", function(){
        spyOn(this.notification_pane, 'markNotificationsRead');
        this.notification_pane.delegateEvents();
        this.mark_notifications_read_target.click();
        expect(this.notification_pane.markNotificationsRead).toHaveBeenCalled();
    });

    it("sets collection url new value after calling markNotificationsRead function", function(){
        // cdodge: we changed behavior of clicking 'mark as read' to only
        // fetch data when we actually have unread notifications
        this.notification_pane.collection.add({'foo': 'bar'});
        this.mark_notifications_read_target.click();
        expect(this.notification_pane.collection.url).toContain('/mark/as/read');
    });

    it("sets selected pane new value after calling markNotificationsRead function", function(){
        this.mark_notifications_read_target.click();
        expect(this.notification_pane.selected_pane).toContain('unread');
    });

    it("calls visitNotification function on clicking notification item", function(){
        var visitNotificationSpy = spyOn(this.notification_pane, 'visitNotification');
        this.notification_pane.delegateEvents();
        /* we don't have any notifications, so the only thing to click on is the empty message */
        this.empty_list_target.click();
        expect(visitNotificationSpy).toHaveBeenCalled();
    });

    it("sets collection url new value after calling visitNotification function", function(){
        this.notification_content_target.click();
        expect(this.notification_pane.collection.url).toContain('read/notifications');
    });

    it("sets notification_content_target.html calling visitNotification function", function(){
        this.notification_content_target.click();
        expect(this.empty_list_target.html()).toContain('You have no unread notifications');
    });

    it("calls preventHidingWhenClickedInside function on clicking .xns-content", function(){
        var preventHidingWhenClickedInsideSpy = spyOn(this.notification_pane, 'preventHidingWhenClickedInside');
        this.notification_pane.delegateEvents();
        this.prevent_click_target.click();
        expect(preventHidingWhenClickedInsideSpy).toHaveBeenCalled();
    });

});
