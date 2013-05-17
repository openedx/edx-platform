if (!CMS.Views['Metadata']) CMS.Views.Metadata = {};

CMS.Views.Metadata.Editor = Backbone.View.extend({

    // Model class is ...
    events : {
    },

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
                        if (item.type === 'Select') {
                            new CMS.Views.Metadata.Option(data);
                        }
                        else if (item.type === 'Integer' || item.type === 'Float') {
                            new CMS.Views.Metadata.Number(data);
                        }
                        else {
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
            // TODO: can we use toggleclass?
            this.$el.find('.setting-clear').removeClass('inactive');
            this.$el.find('.setting-clear').addClass('active');
        }
    },

    render: function () {
        if (!this.template) return;

        this.setValueInEditor(this.model.getDisplayValue());

        if (this.model.isExplicitlySet()) {
            this.showClearButton();
        }
        else {
            this.$el.removeClass('is-set');
            // TODO: can we use toggleclass?
            this.$el.find('.setting-clear').addClass('inactive');
            this.$el.find('.setting-clear').removeClass('active');
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
        "keypress .setting-input" : "showClearButton"  ,
        "click .setting-clear" : "clear"
    },

    render: function () {
        CMS.Views.Metadata.AbstractEditor.prototype.render.apply(this);
        if (!this.inputAttributesSet) {
            var min = "min";
            var max = "max";
            var step = "step";
            var options = this.model.getOptions();
            if (options.hasOwnProperty(min)) {
                this.$el.find('input').attr(min, options[min].toString());
            }
            if (options.hasOwnProperty(max)) {
                this.$el.find('input').attr(max, options[max].toString());
            }
            var stepValue = undefined;
            if (options.hasOwnProperty(step)) {
                stepValue = options[step].toString();
            }
            else if (this.model.getType() === 'Integer') {
                stepValue = "1";
            }
            if (stepValue !== undefined) {
                this.$el.find('input').attr(step, stepValue);
            }
            this.inputAttributesSet = true;
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
