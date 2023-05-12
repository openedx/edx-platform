// eslint-disable-next-line no-undef
define(['backbone', 'underscore'], function(Backbone, _) {
    // eslint-disable-next-line no-var
    var LicenseModel = Backbone.Model.extend({
        defaults: {
            type: null,
            options: {},
            custom: false // either `false`, or a string
        },

        initialize: function(attributes) {
            if (attributes && attributes.asString) {
                this.setFromString(attributes.asString);
                this.unset('asString');
            }
        },

        toString: function() {
            // eslint-disable-next-line no-var
            var custom = this.get('custom');
            if (custom) {
                return custom;
            }

            // eslint-disable-next-line no-var
            var type = this.get('type'),
                options = this.get('options');

            if (_.isEmpty(options)) {
                return type || '';
            }

            // options are where it gets tricky
            // eslint-disable-next-line no-var
            var optionStrings = _.map(options, function(value, key) {
                if (_.isBoolean(value)) {
                    return value ? key : null;
                } else {
                    return key + '=' + value;
                }
            });
            // filter out nulls
            optionStrings = _.filter(optionStrings, _.identity);
            // build license string and return
            return type + ': ' + optionStrings.join(' ');
        },

        setFromString: function(string, options) {
            if (!string) {
                // reset to defaults
                return this.set(this.defaults, options);
            }

            // eslint-disable-next-line no-var
            var colonIndex = string.indexOf(':'),
                spaceIndex = string.indexOf(' ');

            // a string without a colon could be a custom license, or a license
            // type without options
            // eslint-disable-next-line eqeqeq
            if (colonIndex == -1) {
                // eslint-disable-next-line eqeqeq
                if (spaceIndex == -1) {
                    // if there's no space, it's a license type without options
                    return this.set({
                        type: string,
                        options: {},
                        custom: false
                    }, options);
                } else {
                // if there is a space, it's a custom license
                    return this.set({
                        type: null,
                        options: {},
                        custom: string
                    }, options);
                }
            }

            // there is a colon, which indicates a license type with options.
            // eslint-disable-next-line no-var
            var type = string.substring(0, colonIndex),
                optionsObj = {},
                optionsString = string.substring(colonIndex + 1);

            _.each(optionsString.split(' '), function(optionString) {
                if (_.isEmpty(optionString)) {
                    return;
                }
                // eslint-disable-next-line no-var
                var eqIndex = optionString.indexOf('=');
                // eslint-disable-next-line eqeqeq
                if (eqIndex == -1) {
                    // this is a boolean flag
                    optionsObj[optionString] = true;
                } else {
                    // this is a key-value pair
                    // eslint-disable-next-line no-var
                    var optionKey = optionString.substring(0, eqIndex);
                    // eslint-disable-next-line no-var
                    var optionVal = optionString.substring(eqIndex + 1);
                    optionsObj[optionKey] = optionVal;
                }
            });

            return this.set({
                type: type, options: optionsObj, custom: false
            }, options);
        }
    });

    return LicenseModel;
});
