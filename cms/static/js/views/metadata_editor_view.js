if (!CMS.Views['Metadata']) CMS.Views.Metadata = {};

CMS.Views.Metadata.Editor = Backbone.View.extend({

    // Model is simply a Backbone.Model instance.

    initialize : function() {
        var self = this;
        // instantiates an editor template for each update in the collection
        window.templateLoader.loadRemoteTemplate("metadata_editor",
            "/static/client_templates/metadata_editor.html",
            function (raw_template) {
                self.template = _.template(raw_template);
                self.$el.append(self.template({metadata_entries: self.model.attributes}));
                var counter = 0;

                // Sort entries by display name.
                var sortedObject = _.sortBy(self.model.attributes,
                    function (val) {
                        return val.display_name
                    });

                self.models = [];

                _.each(sortedObject,
                    function (item) {
                        var model = new CMS.Models.Metadata(item);
                        self.models.push(model);
                        var data = {
                            el: self.$el.find('.metadata_entry')[counter++],
                            model: model
                        };
                        if (item.type === CMS.Models.Metadata.SELECT_TYPE) {
                            new CMS.Views.Metadata.Option(data);
                        }
                        else if (item.type === CMS.Models.Metadata.INTEGER_TYPE ||
                            item.type === CMS.Models.Metadata.FLOAT_TYPE) {
                            new CMS.Views.Metadata.Number(data);
                        }
                        else {
                            // Everything else is treated as GENERIC_TYPE, which uses String editor.
                            new CMS.Views.Metadata.String(data);
                        }
                    });
            }
        );
    },

    getModifiedMetadataValues: function () {
        var modified_values = {};
        _.each(this.models,
            function (model) {
                if (model.isModified()) {
                    modified_values[model.getFieldName()] = model.getValue();
                }
            }
        );
        return modified_values;
    },

    getDisplayName: function () {
        // It is possible that there is no display name set. In that case, return empty string.
        var displayNameValue = this.model.get('display_name').value;
        return displayNameValue ? displayNameValue : '';
    }
});

CMS.Views.Metadata.AbstractEditor = Backbone.View.extend({

    // Model is CMS.Models.Metadata.

    initialize : function() {
        var self = this;
        var templateName = this.getTemplateName();
        this.uniqueId = _.uniqueId(templateName + "_");
        window.templateLoader.loadRemoteTemplate(templateName,
            "/static/client_templates/" + templateName + ".html",
            function (raw_template) {
                self.template = _.template(raw_template);
                self.$el.append(self.template({model: self.model, uniqueId: self.uniqueId}));
                self.render();
            }
        );
    },

    getTemplateName : function () {},

    getValueFromEditor : function () {},

    setValueInEditor : function (value) {},

    updateModel: function () {
        this.model.setValue(this.getValueFromEditor());
        this.render();
    },

    clear: function () {
        this.model.clear();
        this.render();
    },

    showClearButton: function() {
        if (!this.$el.hasClass('is-set')) {
            this.$el.addClass('is-set');
            this.getClearButton().removeClass('inactive');
            this.getClearButton().addClass('active');
        }
    },

    getClearButton: function () {
        return this.$el.find('.setting-clear');
    },

    render: function () {
        if (!this.template) return;

        this.setValueInEditor(this.model.getDisplayValue());

        if (this.model.isExplicitlySet()) {
            this.showClearButton();
        }
        else {
            this.$el.removeClass('is-set');
            this.getClearButton().addClass('inactive');
            this.getClearButton().removeClass('active');
        }
    }
});

CMS.Views.Metadata.String = CMS.Views.Metadata.AbstractEditor.extend({

    events : {
        "change input" : "updateModel",
        "keypress .setting-input" : "showClearButton"  ,
        "click .setting-clear" : "clear"
    },

    getTemplateName : function () {
        return "metadata_string_entry";
    },

    getValueFromEditor : function () {
        return this.$el.find('#' + this.uniqueId).val();
    },

    setValueInEditor : function (value) {
        this.$el.find('input').val(value);
    }
});

CMS.Views.Metadata.Number = CMS.Views.Metadata.AbstractEditor.extend({

    events : {
        "change input" : "updateModel",
        "keypress .setting-input" : "keyPressed",
        "change .setting-input" : "changed",
        "click .setting-clear" : "clear"
    },

    render: function () {
        CMS.Views.Metadata.AbstractEditor.prototype.render.apply(this);
        if (!this.initialized) {
            var numToString = function (val) {
                return val.toFixed(4);
            };
            var min = "min";
            var max = "max";
            var step = "step";
            var options = this.model.getOptions();
            if (options.hasOwnProperty(min)) {
                this.min = Number(options[min]);
                this.$el.find('input').attr(min, numToString(this.min));
            }
            if (options.hasOwnProperty(max)) {
                this.max = Number(options[max]);
                this.$el.find('input').attr(max, numToString(this.max.toFixed));
            }
            var stepValue = undefined;
            if (options.hasOwnProperty(step)) {
                // Parse step and convert to String. Polyfill doesn't like float values like ".1" (expects "0.1").
                stepValue = numToString(Number(options[step]));
            }
            else if (this.isIntegerField()) {
                stepValue = "1";
            }
            if (stepValue !== undefined) {
                this.$el.find('input').attr(step, stepValue);
            }

            //   Manually runs polyfill for input number types to correct for Firefox non-support
            this.$el.find('.setting-input-number').inputNumber();

            this.initialized = true;
        }
    },

    getTemplateName : function () {
        return "metadata_number_entry";
    },

    getValueFromEditor : function () {
        return this.$el.find('#' + this.uniqueId).val();
    },

    setValueInEditor : function (value) {
        this.$el.find('input').val(value);
    },

    isIntegerField : function () {
        return this.model.getType() === 'Integer';
    },

    keyPressed: function (e) {
        this.showClearButton();
        // This first filtering if statement is take from polyfill to prevent
        // non-numeric input (for browsers that don't use polyfill because they DO have a number input type).
        var _ref, _ref1;
        if (((_ref = e.keyCode) !== 8 && _ref !== 9 && _ref !== 35 && _ref !== 36 && _ref !== 37 && _ref !== 39) &&
            ((_ref1 = e.which) !== 45 && _ref1 !== 46 && _ref1 !== 48 && _ref1 !== 49 && _ref1 !== 50 && _ref1 !== 51
                && _ref1 !== 52 && _ref1 !== 53 && _ref1 !== 54 && _ref1 !== 55 && _ref1 !== 56 && _ref1 !== 57)) {
            e.preventDefault();
        }
        // For integers, prevent decimal points.
        if (this.isIntegerField() && e.keyCode === 46) {
            e.preventDefault();
        }
    },

    changed: function () {
        // Limit value to the range specified by min and max (necessary for browsers that aren't using polyfill).
        var value = this.getValueFromEditor();
        if ((this.max !== undefined) && value > this.max) {
            value = this.max;
        } else if ((this.min != undefined) && value < this.min) {
            value = this.min;
        }
        this.setValueInEditor(value);
    }

});


CMS.Views.Metadata.Option = CMS.Views.Metadata.AbstractEditor.extend({

    events : {
        "change select" : "updateModel",
        "click .setting-clear" : "clear"
    },

    getTemplateName : function () {
        return "metadata_option_entry";
    },

    getValueFromEditor : function () {
        var selectedText = this.$el.find('#' + this.uniqueId).find(":selected").text();
        var selectedValue;
        _.each(this.model.getOptions(), function (modelValue) {
            if (modelValue === selectedText) {
                selectedValue = modelValue;
            }
            else if (modelValue['display_name'] === selectedText) {
                selectedValue = modelValue['value'];
            }
        });
        return selectedValue;
    },

    setValueInEditor : function (value) {
        // Value here is the json value as used by the field. The choice may instead be showing display names.
        // Find the display name matching the value passed in.
        _.each(this.model.getOptions(), function (modelValue) {
            if (modelValue['value'] === value) {
                value = modelValue['display_name'];
            }
        });
        $('#' + this.uniqueId + " option").filter(function() {
            return $(this).text() === value;
        }).prop('selected', true);
    }
});
