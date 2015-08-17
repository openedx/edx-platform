// Backbone Application View: Certificate Preview
// User can preview the certificate web layout/styles. 'Preview Certificate' button will open a new tab in LMS for
// the selected course mode from the drop down.

define([ // jshint ignore:line
    'underscore',
    'gettext',
    'js/views/baseview',
    'js/views/utils/view_utils',
    'js/views/feedback_notification'
],
function(_, gettext, BaseView, ViewUtils, NotificationView) {
    'use strict';
    var CertificateWebPreview = BaseView.extend({
        el: $(".preview-certificate"),
        events: {
            "change #course-modes": "courseModeChanged",
            "click .activate-cert": "toggleCertificateActivation"
        },

        initialize: function (options) {
            this.course_modes = options.course_modes;
            this.certificate_web_view_url = options.certificate_web_view_url;
            this.certificate_activation_handler_url = options.certificate_activation_handler_url;
            this.is_active = options.is_active;
            this.template = this.loadTemplate('certificate-web-preview');
        },

        render: function () {
            this.$el.html(this.template({
                course_modes: this.course_modes,
                certificate_web_view_url: this.certificate_web_view_url,
                is_active: this.is_active
            }));
            return this;
        },

        toggleCertificateActivation: function() {
            var msg = "Activating";
            if(this.is_active) {
                msg = "Deactivating";
            }

            var notification = new NotificationView.Mini({
                title: gettext(msg)
            });

            $.ajax({
                url: this.certificate_activation_handler_url,
                type: "POST",
                dataType: "json",
                contentType: "application/json",
                data: JSON.stringify({
                    is_active: !this.is_active
                }),
                beforeSend: function() {
                    notification.show();
                },
                success: function(){
                    notification.hide();
                    location.reload();
                }
            });
        },

        courseModeChanged: function (event) {
            $('.preview-certificate-link').attr('href', function(index, value){
                return value.replace(/preview=([^&]+)/, function() {
                    return 'preview=' + event.target.options[event.target.selectedIndex].text;
                });
            });
        },

        show: function() {
            this.render();
        },

        remove: function() {
            this.is_active = false;
            this.$el.empty();
            return this;
        }
    });
    return CertificateWebPreview;
});
