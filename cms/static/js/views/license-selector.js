/**
 * Provide license selector view for license models.
 * These license selectors are used to set the license for
 * new or existing courses and videos.
 */
define(["js/views/baseview", "underscore", "gettext", "js/models/license", "js/views/license-view"],
    function(BaseView, _, gettext, LicenseModel, LicenseView) {

        var LicenseSelector = BaseView.extend({
            events: {
                "click .license-button" : "onLicenseButtonClick",
            },

            initialize: function(options) {
                this.template = this.loadTemplate("license-selector");

                // Rerender on model change
                this.listenTo(this.model, 'change', this.render);
                this.render();
            },

            render: function() {
                this.$el.html(this.template({
                    kind: this.model.get('kind'),
                }));

                this.licenseView = new LicenseView({
                    model: this.model,
                    el: document.getElementById("license-preview")
                });

                return this;
            },

            onLicenseButtonClick: function(e) {
                var $button, buttonLicenseKind;

                $button = $(e.srcElement || e.target).closest('.license-button');
                buttonLicenseKind = $button.attr("data-license");

                this.model.toggleAttribute(buttonLicenseKind);

                return this;
            },

        });

        return LicenseSelector;
    }
); // end define();
