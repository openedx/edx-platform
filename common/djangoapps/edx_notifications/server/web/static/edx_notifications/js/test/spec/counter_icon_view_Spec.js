describe("CounterIconView", function(){

    beforeEach(function(){
        this.server = sinon.fakeServer.create();
        jasmine.clock().install();
        setFixtures(
            '<div><img class="xns-icon" src="/static/edx_notifications/img/notification_icon.jpg" />' +
            '<span class="xns-counter"></span> </div>' +
            '<div class="xns-pane">' +
            '<script type="text/template" id="xns-counter-template">' +
                '<% if (typeof count !== "undefined" && count > 0) { %>' +
                '<%= count %><% } %>' +
            '</script>'
        );
        this.counter_view = new CounterIconView({
            el: $(".xns-icon"),
            count_el: $(".xns-counter"),
            pane_el: $(".xns-pane"),
            endpoints: {
                unread_notification_count: "/unread/count/?read=False&unread=True",
                mark_all_user_notifications_read: "mark/as/read",
                user_notifications_all:"all/notifications/?read=True&unread=True",
                user_notifications_unread_only: "unread/notifications/?read=False&unread=True",
                renderer_templates_urls: "/renderer/templates",
                user_notification_mark_read: "notification/mark/read"
            },
            global_variables: {
                app_name: "mcka",
                hide_link_is_visible: "false",
                always_show_dates_on_unread: "false"

            },
            refresh_watcher: {
                name: "none",
                args: {
                    poll_period_secs: 1
                }
            },
            view_audios: {
                notification_alert: "chirp"
            },

            namespace: "/foo/bar/baz"
        });
        this.counter_view.render();
    });

    afterEach(function() {
        this.server.restore();
        jasmine.clock().uninstall();
    });

    it("assigns value to namespace", function(){
        expect(this.counter_view.namespace).toBe('/foo/bar/baz')
    });

    it("assigns value to audio", function(){
        expect(this.counter_view.view_audios.notification_alert).toBe('chirp')
    });

    it("initializes value to globalapp name", function(){
        expect(this.counter_view.global_variables.app_name).toBe('mcka')
    });

    it("initializes value to global hide_link variable", function(){
        expect(this.counter_view.global_variables.hide_link_is_visible).toBe('false')
    });

    it("initializes value to global show dates variables", function(){
        expect(this.counter_view.global_variables.always_show_dates_on_unread).toBe('false')
    });

    it("initializes value to refresh watchers", function(){
        expect(this.counter_view.refresh_watcher.args.poll_period_secs).toBe(1)
    });

    it("assigns unread notifications count url with name space as model url", function(){
        expect(this.counter_view.model.url).toBe('/unread/count/?read=False&unread=True&namespace=%2Ffoo%2Fbar%2Fbaz')
    });

    it("checks if template function is defined", function(){
        expect(this.counter_view.template).toBeDefined()
    });

    it("returns unread_notification_count url in endpoint", function(){
        expect(this.counter_view.endpoints.unread_notification_count).toEqual('/unread/count/?read=False&unread=True');
    });

    it("returns mark_all_user_notifications_read url in endpoint", function(){
        expect(this.counter_view.endpoints.mark_all_user_notifications_read).toEqual('mark/as/read');
    });

    it("returns all_notifications url in endpoint", function(){
        expect(this.counter_view.endpoints.user_notifications_all).toBe('all/notifications/?read=True&unread=True');
    });

    it("returns unread_notifications url in endpoint", function(){
        expect(this.counter_view.endpoints.user_notifications_unread_only).toContain('unread/notifications/');
    });

    it("returns renderer_templates_urls in endpoints", function(){
        expect(this.counter_view.endpoints.renderer_templates_urls).toEqual('/renderer/templates');
    });

    it("returns notification mark read url in endpoints", function(){
        expect(this.counter_view.endpoints.user_notification_mark_read).toEqual('notification/mark/read');
    });

    it("returns notification icon class in el", function(){
        expect(this.counter_view.$el).toContain('.xns-icon')
    });

    it("calls showPane function on clicking notification icon", function(){
        var target = $(".xns-icon");
        var showPaneSpy = spyOn(this.counter_view, 'showPane');
        this.counter_view.delegateEvents();
        target.click();
        expect(showPaneSpy).toHaveBeenCalled();
    });

    it("does not call autoRefreshNotification if refresh watcher name is not short-poll", function(){
        var autoRefreshSpy  = spyOn(this.counter_view, 'autoRefreshNotifications');
        expect(autoRefreshSpy).not.toHaveBeenCalled()
    });

    it("calls autoRefresh.. if refresh_watcher name is short-poll and interval>=2000", function(){
        var autoRefreshSpy  = spyOn(CounterIconView.prototype, 'autoRefreshNotifications');
        var protoView = new CounterIconView({
            el: $(".xns-icon"),
            count_el: $(".xns-counter"),
            endpoints: {
                unread_notification_count: "/unread/count/?read=False&unread=True"
            },
            refresh_watcher: {
                name: "short-poll",
                args: {
                    poll_period_secs: 2
                }
            }
        });
        jasmine.clock().tick(1999);
        expect(autoRefreshSpy).not.toHaveBeenCalled();
        jasmine.clock().tick(2000);
        expect(autoRefreshSpy).toHaveBeenCalled();
    });

});