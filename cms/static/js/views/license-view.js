/**
 * Provide license display view for license models.
 * The license display view is used to preview the selected license in
 * forms for new or existing courses and videos. Additionally, the display
 * view is used to preview the license underneath videos and inside the
 * course outline. Such that the author knows under which license the
 * course material will be published.
 */
define(["js/views/baseview", "underscore", "gettext", "js/models/license"],
    function(BaseView, _, gettext, LicenseModel) {

        var LicenseView = BaseView.extend({
            initialize: function(options) {
                this.template = this.loadTemplate("license-view");
                // Rerender on model change
                this.listenTo(this.model, 'change', this.render);
                this.render();
            },

            render: function() {
                this.$el.html(this.template({
                    kind: this.model.get('kind'),
                    version: this.model.get('version'),
                    cc_tooltip: this.renderCCLicenseTooltip(),
                }));

                return this;
            },

            renderCCLicenseTooltip: function() {
                var kind, licenseText;
                kind = this.model.get('kind');

                // Creative commons license
                licenseText = [];
                if(/BY/.exec(kind)){
                    // Translators: This license attribute should follow the standards
                    // as specified by the Creative Commons organisation.
                    // For example, see: http://creativecommons.org/licenses/by-nc-nd/4.0/
                    licenseText.push(gettext("Attribution"));
                }
                if(/NC/.exec(kind)){
                    // Translators: This license attribute should follow the standards
                    // as specified by the Creative Commons organisation.
                    // For example, see: http://creativecommons.org/licenses/by-nc-nd/4.0/
                    licenseText.push(gettext("NonCommercial"));
                }
                if(/SA/.exec(kind)){
                    // Translators: This license attribute should follow the standards
                    // as specified by the Creative Commons organisation.
                    // For example, see: http://creativecommons.org/licenses/by-nc-nd/4.0/
                    licenseText.push(gettext("ShareAlike"));
                }
                if(/ND/.exec(kind)){
                    // Translators: This license attribute should follow the standards
                    // as specified by the Creative Commons organisation.
                    // For example, see: http://creativecommons.org/licenses/by-nc-nd/4.0/
                    licenseText.push(gettext("NonDerivatives"));
                }
                // Translators: This license attributes variable will be defined according to
                // license flags that are set. Each of the attributes are translated, and concatenated
                // with dashes. This is according to the license definition of Creative Commons.
                return interpolate(gettext("This work is licensed under a Creative Commons %(license_attributes)s %(version)s International License."), {
                        license_attributes: licenseText.join("-"),
                        version: this.model.get('version')
                    }, true);
            },

        });

        return LicenseView;
    }
); // end define();
