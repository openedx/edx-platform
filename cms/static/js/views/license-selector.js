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
                if (!this.model) {
                    this.model = new LicenseModel();
                }
                else if (!(this.model instanceof LicenseModel) && this.model.kind) {
                    this.model = new LicenseModel(this.model);
                }
                this.licenseView = new LicenseView({
                    model: this.model
                });

                // Rerender on model change
                this.listenTo(this.model, 'change', this.render);
                this.render();
            },

            render: function() {
                this.$el.html(this.template({
                    license_data: this.model.get('kind'),
                    license_preview: this.licenseView.renderLicense()
                }));

                this.$el.addClass('license-selector');

                this.renderLicenseButtons();

                return this;
            },

            renderLicenseButtons: function() {
                var kind, $cc;
                kind = this.model.get('kind');
                $cc = this.$el.find('.selected-cc-license-options');

                if (!kind || kind === "NONE" || kind === "ARR") {
                    this.$el.find('.license-button[data-license="ARR"]').addClass('selected');
                    this.$el.find('.license-button[data-license="CC"]').removeClass('selected');
                    $cc.hide();
                }
                else {
                    var attr = kind.split("-");
                    this.$el.find('.license-button').removeClass('selected');
                    for(i in attr) {
                        this.$el.find('.license-button[data-license="' + attr[i] + '"]').addClass('selected');
                    }
                    $cc.show();
                }

                return this;
            },

            onLicenseButtonClick: function(e) {
                var $button, $cc, buttonLicenseKind, licenseKind, selected;

                $button = $(e.srcElement || e.target).closest('.license-button');
                $cc = this.$el.find('.license-cc-options');
                buttonLicenseKind = $button.attr("data-license");

                if(buttonLicenseKind === "ARR"){
                    licenseKind = buttonLicenseKind;
                }
                else {
                    if($button.hasClass('selected') && (buttonLicenseKind === "CC" || buttonLicenseKind === "BY")){
                        // Abort, this attribute is not allowed to be unset through another click
                        return this;
                    }
                    $button.toggleClass("selected");

                    if (buttonLicenseKind === "ND" && $button.hasClass("selected")) {
                        $cc.children(".license-button[data-license='SA']").removeClass("selected");
                    }
                    else if(buttonLicenseKind === "SA" && $button.hasClass("selected")) {
                        $cc.children(".license-button[data-license='ND']").removeClass("selected");
                    }

                    licenseKind = "CC";
                    $cc.children(".license-button[data-license='BY']").addClass("selected");
                    selected = $cc.children(".selected");
                    selected.each( function() {
                        licenseKind = licenseKind + "-" + $(this).attr("data-license");
                    });
                }

                this.model.set('kind', licenseKind);

                return this;
            },

        });

        return LicenseSelector;
    }
); // end define();
