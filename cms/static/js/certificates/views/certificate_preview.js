// Backbone Application View: Certificate Preview
// User can preview the certificate web layout/styles. 'Preview Certificate' button will open a new tab in LMS for
// the selected course mode from the drop down.

define([
    'underscore',
    'js/views/baseview'
],
function(_, BaseView) {
    'use strict';
    var CertificateWebPreview = BaseView.extend({
        el: $(".preview-certificate"),
        events: {
            "change #course-modes": "courseModeChanged"
        },

        initialize: function (options) {
            this.course_modes = options.course_modes;
            this.certificate_web_view_url = options.certificate_web_view_url;
            this.template = this.loadTemplate('certificate-web-preview');
        },

        render: function () {
            this.$el.html(this.template({
                    course_modes: this.course_modes,
                    certificate_web_view_url: this.certificate_web_view_url
                }));
            return this;
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
            this.$el.empty();
            return this;
        }
    });
    return CertificateWebPreview;
});