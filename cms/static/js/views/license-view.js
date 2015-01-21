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
                if (!this.model) {
                    this.model = new LicenseModel();
                }
                else if (!(this.model instanceof LicenseModel)) {
                    if (this.model.get('license') instanceof LicenseModel) {
                        this.model = this.model.get('license');
                    } else {
                        this.model = new LicenseModel({kind: this.model.get('license')});
                    }
                }

                // Rerender on model change
                this.listenTo(this.model, 'change', this.render);
                this.render();
            },

            render: function() {
                this.$el.html(this.renderLicense());

                return this;
            },

            renderLicense: function() {
                var kind, licenseHtml, licenseText, licenseLink, licenseTooltip, licenseVersion;
                kind = (this.model.get('kind') || "NONE");

                if(kind === "NONE" || kind === "ARR"){
                    // All rights reserved
                    licenseText = gettext("All rights reserved")
                    return "&copy;<span class='license-text'>" + licenseText + "</span>";
                }
                else if(kind === "CC0"){
                    // Creative commons zero license
                    licenseText = gettext("No rights reserved")
                    return "<a rel='license' href='http://creativecommons.org/publicdomain/zero/1.0/' target='_blank'><i class='icon-cc'></i><i class='icon-cc-zero'></i><span class='license-text'>" + licenseText + "</span></a>";
                }
                else {
                    // Creative commons license
                    licenseVersion = "4.0";
                    licenseHtml = "<i class='icon-cc'></i>";
                    licenseLink = [];
                    licenseText = [];
                    if(/BY/.exec(kind)){
                        licenseHtml += "<i class='icon-cc-by'></i>";
                        licenseLink.push("by");
                        // Translators: This license attribute should follow the standards
                        // as specified by the Creative Commons organisation.
                        // For example, see: http://creativecommons.org/licenses/by-nc-nd/4.0/
                        licenseText.push(gettext("Attribution"));
                    }
                    if(/NC/.exec(kind)){
                        licenseHtml += "<i class='icon-cc-nc'></i>";
                        licenseLink.push("nc");
                        // Translators: This license attribute should follow the standards
                        // as specified by the Creative Commons organisation.
                        // For example, see: http://creativecommons.org/licenses/by-nc-nd/4.0/
                        licenseText.push(gettext("NonCommercial"));
                    }
                    if(/SA/.exec(kind)){
                        licenseHtml += "<i class='icon-cc-sa'></i>";
                        licenseLink.push("sa");
                        // Translators: This license attribute should follow the standards
                        // as specified by the Creative Commons organisation.
                        // For example, see: http://creativecommons.org/licenses/by-nc-nd/4.0/
                        licenseText.push(gettext("ShareAlike"));
                    }
                    if(/ND/.exec(kind)){
                        licenseHtml += "<i class='icon-cc-nd'></i>";
                        licenseLink.push("nd");
                        // Translators: This license attribute should follow the standards
                        // as specified by the Creative Commons organisation.
                        // For example, see: http://creativecommons.org/licenses/by-nc-nd/4.0/
                        licenseText.push(gettext("NonDerivatives"));
                    }
                    licenseTooltip = interpolate(gettext("This work is licensed under a Creative Commons %(license_attributes)s %(version)s International License."), {
                            license_attributes: licenseText.join("-"),
                            version: licenseVersion
                        }, true);
                    return "<a rel='license' href='http://creativecommons.org/licenses/" +
                        licenseLink.join("-") + "/" + licenseVersion + "/' data-tooltip='" + licenseTooltip +
                        "' target='_blank' class='license'>" +
                        licenseHtml +
                        "<span class='license-text'>" +
                        gettext("Some rights reserved") +
                        "</span></a>";
                }
            },

        });

        return LicenseView;
    }
); // end define();
