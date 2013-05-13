if (!CMS.Views['Metadata']) CMS.Views.Metadata = {};

CMS.Views.Metadata.Editor = Backbone.View.extend({

    // Model class is ...
    events : {
    },

    views : {}, // child views

    initialize : function() {
        var self = this;
        // instantiates an editor template for each update in the collection
        window.templateLoader.loadRemoteTemplate("metadata_editor",
            "/static/client_templates/metadata_editor.html",
            function (raw_template) {
                self.template = _.template(raw_template);
                self.$el.append(self.template({metadata_entries: self.model.attributes}));
                var counter = 0;
                _.each(self.model.attributes,
                    function(item, key) {
                        var data = {
                            el: self.$el.find('.metadata_entry')[counter++],
                            model: new CMS.Models.Metadata(item)
                        };
                        if (item.options.length > 0) {
                            // Right now, all our option types only hold strings. Should really support
                            // any type though.
                            self.views[key] = new CMS.Views.Metadata.Option(data);
                        }
                        else {
                            self.views[key] = new CMS.Views.Metadata.String(data);
                        }

                    });
            }
        );
    },

    getModifiedMetadataValues: function () {
        var modified_values = {};
        _.each(this.views,
            function (item, key) {
                if (item.modified()) {
                    modified_values[key] = item.getValue();
                }
            }
        );
        return modified_values;
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
    },


    modified: function () {
        return this.model.isModified();
    },

    getValue: function() {
        return this.model.getValue();
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
        var val = this.$el.find('#' + this.uniqueId).val();
//      TODO: not sure this is necessary. Trying to support empty value ("").
        return val ? val : "";
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
        return this.$el.find('#' + this.uniqueId).find(":selected").text();
    },

    setValueInEditor : function (value) {
        $('#' + this.uniqueId + " option").filter(function() {
            return $(this).text() === value;
        }).prop('selected', true);
    }
});



