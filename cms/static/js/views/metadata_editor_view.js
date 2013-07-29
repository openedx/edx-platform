if (!CMS.Views['Metadata']) CMS.Views.Metadata = {};

CMS.Views.Metadata.Editor = Backbone.View.extend({

    // Model is CMS.Models.MetadataCollection,
    initialize : function() {
        var tpl = $("#metadata-editor-tpl").text();
        if(!tpl) {
            console.error("Couldn't load metadata editor template");
        }
        this.template = _.template(tpl);

        this.$el.html(this.template({numEntries: this.collection.length}));
        var counter = 0;

        var self = this;
        this.collection.each(
            function (model) {
                var data = {
                    el: self.$el.find('.metadata_entry')[counter++],
                    model: model
                };
                if (model.getType() === CMS.Models.Metadata.SELECT_TYPE) {
                    new CMS.Views.Metadata.Option(data);
                }
                else if (model.getType() === CMS.Models.Metadata.INTEGER_TYPE ||
                    model.getType() === CMS.Models.Metadata.FLOAT_TYPE) {
                    new CMS.Views.Metadata.Number(data);
                }
                else if(model.getType() === CMS.Models.Metadata.LIST_TYPE) {
                    new CMS.Views.Metadata.List(data);
                }
                else {
                    // Everything else is treated as GENERIC_TYPE, which uses String editor.
                    new CMS.Views.Metadata.String(data);
                }
            });
    },

    /**
     * Returns the just the modified metadata values, in the format used to persist to the server.
     */
    getModifiedMetadataValues: function () {
        var modified_values = {};
        this.collection.each(
            function (model) {
                if (model.isModified()) {
                    modified_values[model.getFieldName()] = model.getValue();
                }
            }
        );
        return modified_values;
    },

    /**
     * Returns a display name for the component related to this metadata. This method looks to see
     * if there is a metadata entry called 'display_name', and if so, it returns its value. If there
     * is no such entry, or if display_name does not have a value set, it returns an empty string.
     */
    getDisplayName: function () {
        var displayName = '';
        this.collection.each(
            function (model) {
                if (model.get('field_name') === 'display_name') {
                    var displayNameValue = model.get('value');
                    // It is possible that there is no display name value set. In that case, return empty string.
                    displayName = displayNameValue ? displayNameValue : '';
                }
            }
        );
        return displayName;
    }
});

CMS.Views.Metadata.AbstractEditor = Backbone.View.extend({

    // Model is CMS.Models.Metadata.
    initialize : function() {
        var self = this;
        var templateName = _.result(this, 'templateName');
        // Backbone model cid is only unique within the collection.
        this.uniqueId = _.uniqueId(templateName + "_");

        var tpl = document.getElementById(templateName).text;
        if(!tpl) {
            console.error("Couldn't load template: " + templateName);
        }
        this.template = _.template(tpl);
        this.$el.html(this.template({model: this.model, uniqueId: this.uniqueId}));
        this.listenTo(this.model, 'change', this.render);
        this.render();
    },

    /**
     * The ID/name of the template. Subclasses must override this.
     */
    templateName: '',

    /**
     * Returns the value currently displayed in the editor/view. Subclasses should implement this method.
     */
    getValueFromEditor : function () {},

    /**
     * Sets the value currently displayed in the editor/view. Subclasses should implement this method.
     */
    setValueInEditor : function (value) {},

    /**
     * Sets the value in the model, using the value currently displayed in the view.
     */
    updateModel: function () {
        this.model.setValue(this.getValueFromEditor());
    },

    /**
     * Clears the value currently set in the model (reverting to the default).
     */
    clear: function () {
        this.model.clear();
    },

    /**
     * Shows the clear button, if it is not already showing.
     */
    showClearButton: function() {
        if (!this.$el.hasClass('is-set')) {
            this.$el.addClass('is-set');
            this.getClearButton().removeClass('inactive');
            this.getClearButton().addClass('active');
        }
    },

    /**
     * Returns the clear button.
     */
    getClearButton: function () {
        return this.$el.find('.setting-clear');
    },

    /**
     * Renders the editor, updating the value displayed in the view, as well as the state of
     * the clear button.
     */
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

        return this;
    }
});

CMS.Views.Metadata.String = CMS.Views.Metadata.AbstractEditor.extend({

    events : {
        "change input" : "updateModel",
        "keypress .setting-input" : "showClearButton"  ,
        "click .setting-clear" : "clear"
    },

    templateName: "metadata-string-entry",

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
                this.$el.find('input').attr(max, numToString(this.max));
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

            // Manually runs polyfill for input number types to correct for Firefox non-support.
            // inputNumber will be undefined when unit test is running.
            if ($.fn.inputNumber) {
                this.$el.find('.setting-input-number').inputNumber();
            }

            this.initialized = true;
        }

        return this;
    },

    templateName: "metadata-number-entry",

    getValueFromEditor : function () {
        return this.$el.find('#' + this.uniqueId).val();
    },

    setValueInEditor : function (value) {
        this.$el.find('input').val(value);
    },

    /**
     * Returns true if this view is restricted to integers, as opposed to floating points values.
     */
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
        this.updateModel();
    }

});

CMS.Views.Metadata.Option = CMS.Views.Metadata.AbstractEditor.extend({

    events : {
        "change select" : "updateModel",
        "click .setting-clear" : "clear"
    },

    templateName: "metadata-option-entry",

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
        this.$el.find('#' + this.uniqueId + " option").filter(function() {
            return $(this).text() === value;
        }).prop('selected', true);
    }
});

CMS.Views.Metadata.List = CMS.Views.Metadata.AbstractEditor.extend({

    events : {
        "click .setting-clear" : "clear",
        "keypress .setting-input" : "showClearButton",
        "change input" : "updateModel",
        "click .create-setting" : "addEntry",
        "click .remove-setting" : "removeEntry"
    },

    templateName: "metadata-list-entry",

    getValueFromEditor: function () {
        return _.map(
            this.$el.find('li input'),
            function (ele) { return ele.value.trim(); }
        ).filter(_.identity);
    },

    setValueInEditor: function (value) {
        var list = this.$el.find('ol');
        list.empty();
        _.each(value, function(ele, index) {
            var template = _.template(
                '<li class="list-settings-item">' +
                    '<input class="input" value="<%= ele %>">' +
                    '<a href="#" class="remove-action remove-setting" data-index="<%= index %>"><i class="icon-remove-sign"></i><span class="sr">Remove</span></a>' +
                '</li>'
            );
            list.append($(template({'ele': ele, 'index': index})));
        });
    },

    addEntry: function(event) {
        event.preventDefault();
        // We don't call updateModel here since it's bound to the
        // change event
        var list = this.model.get('value') || [];
        this.setValueInEditor(list.concat(['']))
    },

    removeEntry: function(event) {
        event.preventDefault();
        var entry = $(event.currentTarget).siblings().val();
        this.setValueInEditor(_.without(this.model.get('value'), entry));
        this.updateModel();
    }
});
