define([
    'js/views/baseview',
    'underscore',
    'text!templates/license-selector.underscore'
], function(BaseView, _, licenseSelectorTemplate) {
    var defaultLicenseInfo = {
        'all-rights-reserved': {
            'name': gettext('All Rights Reserved'),
            'tooltip': gettext('You reserve all rights for your work')
        },
        'creative-commons': {
            'name': gettext('Creative Commons'),
            'tooltip': gettext('You waive some rights for your work, such that others can use it too'),
            'url': 'https://creativecommons.org/about',
            'options': {
                'ver': {
                    'name': gettext('Version'),
                    'type': 'string',
                    'default': '4.0'
                },
                'BY': {
                    'name': gettext('Attribution'),
                    'type': 'boolean',
                    'default': true,
                    'help': gettext('Allow others to copy, distribute, display and perform your copyrighted work but only if they give credit the way you request. Currently, this option is required.'),
                    'disabled': true
                },
                'NC': {
                    'name': gettext('Noncommercial'),
                    'type': 'boolean',
                    'default': true,
                    'help': gettext('Allow others to copy, distribute, display and perform your work - and derivative works based upon it - but for noncommercial purposes only.')
                },
                'ND': {
                    'name': gettext('No Derivatives'),
                    'type': 'boolean',
                    'default': true,
                    'help': gettext('Allow others to copy, distribute, display and perform only verbatim copies of your work, not derivative works based upon it. This option is incompatible with "Share Alike".'),
                    'conflictsWith': ['SA']
                },
                'SA': {
                    'name': gettext('Share Alike'),
                    'type': 'boolean',
                    'default': false,
                    'help': gettext('Allow others to distribute derivative works only under a license identical to the license that governs your work. This option is incompatible with "No Derivatives".'),
                    'conflictsWith': ['ND']
                }
            },
            'option_order': ['BY', 'NC', 'ND', 'SA']
        }
    };

    var LicenseView = BaseView.extend({
        events: {
            'click ul.license-types li button': 'onLicenseClick',
            'click ul.license-options li': 'onOptionClick'
        },

        initialize: function(options) {
            this.licenseInfo = options.licenseInfo || defaultLicenseInfo;
            this.showPreview = !!options.showPreview; // coerce to boolean

            // Rerender when the model changes
            this.listenTo(this.model, 'change', this.render);
            this.render();
        },

        getDefaultOptionsForLicenseType: function(licenseType) {
            if (!this.licenseInfo[licenseType]) {
                // custom license type, no options
                return {};
            }
            if (!this.licenseInfo[licenseType].options) {
                // defined license type without options
                return {};
            }
            var defaults = {};
            _.each(this.licenseInfo[licenseType].options, function(value, key) {
                defaults[key] = value.default;
            });
            return defaults;
        },

        render: function() {
            this.$el.html(_.template(licenseSelectorTemplate)({
                model: this.model.attributes,
                licenseString: this.model.toString() || '',
                licenseInfo: this.licenseInfo,
                showPreview: this.showPreview,
                previewButton: false
            }));
            return this;
        },

        onLicenseClick: function(e) {
            var $li = $(e.srcElement || e.target).closest('li');
            var licenseType = $li.data('license');

            // Check that we've selected a different license type than what's currently selected
            if (licenseType != this.model.attributes.type) {
                this.model.set({
                    type: licenseType,
                    options: this.getDefaultOptionsForLicenseType(licenseType)
                });
                // Fire the change event manually
                this.model.trigger('change change:type');
            }
            e.preventDefault();
        },

        onOptionClick: function(e) {
            var licenseType = this.model.get('type'),
                licenseOptions = $.extend({}, this.model.get('options')),
                $li = $(e.srcElement || e.target).closest('li');

            var optionKey = $li.data('option');
            var licenseInfo = this.licenseInfo[licenseType];
            var optionInfo = licenseInfo.options[optionKey];
            if (optionInfo.disabled) {
                // we're done here
                return;
            }
            var currentOptionValue = licenseOptions[optionKey];
            if (optionInfo.type === 'boolean') {
                // toggle current value
                currentOptionValue = !currentOptionValue;
                licenseOptions[optionKey] = currentOptionValue;
            }
            // check for conflicts
            if (currentOptionValue && optionInfo.conflictsWith) {
                var conflicts = optionInfo.conflictsWith;
                for (var i = 0; i < conflicts.length; i++) {
                    // Uncheck all conflicts
                    licenseOptions[conflicts[i]] = false;
                    console.log(licenseOptions);
                }
            }

            this.model.set({'options': licenseOptions});
            // Backbone has trouble identifying when objects change, so we'll
            // fire the change event manually.
            this.model.trigger('change change:options');
            e.preventDefault();
        }

    });
    return LicenseView;
});
