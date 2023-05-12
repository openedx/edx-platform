// eslint-disable-next-line no-undef
define(['backbone', 'gettext', 'common/js/components/views/feedback_notification', 'js/utils/module'],
    function(Backbone, gettext, NotificationView, ModuleUtils) {
        // eslint-disable-next-line no-var
        var Section = Backbone.Model.extend({
            defaults: {
                name: ''
            },
            /* eslint-disable-next-line consistent-return, no-unused-vars */
            validate: function(attrs, options) {
                if (!attrs.name) {
                    return gettext('You must specify a name');
                }
            },
            urlRoot: ModuleUtils.urlRoot,
            toJSON: function() {
                return {
                    metadata: {
                        display_name: this.get('name')
                    }
                };
            },
            initialize: function() {
                this.listenTo(this, 'request', this.showNotification);
                this.listenTo(this, 'sync', this.hideNotification);
            },
            showNotification: function() {
                if (!this.msg) {
                    this.msg = new NotificationView.Mini({
                        title: gettext('Saving')
                    });
                }
                this.msg.show();
            },
            hideNotification: function() {
                if (!this.msg) { return; }
                this.msg.hide();
            }
        });
        return Section;
    });
