if (!CMS.Views['Settings']) CMS.Views.Settings = {};

CMS.Views.Settings.Advanced = CMS.Views.ValidatingView.extend({
    error_saving : "error_saving",
    successful_changes: "successful_changes",

    // Model class is CMS.Models.Settings.Advanced
    events : {
        'click .delete-button' : "deleteEntry",
        'click .new-button' : "addEntry",
        // update model on changes
        'change .policy-key' : "updateKey",
        'keydown .policy-key' : "showSaveCancelButtons"
        // TODO enable/disable save based on validation (currently enabled whenever there are changes)
    },
    initialize : function() {
        var self = this;
        // instantiates an editor template for each update in the collection
        window.templateLoader.loadRemoteTemplate("advanced_entry",
            "/static/client_templates/advanced_entry.html",
            function (raw_template) {
                self.template = _.template(raw_template);
                self.render();
            }
        );
        $('.save-button').on('click', this, this.saveView);
        $('.cancel-button').on('click', this, this.revertView);
        this.model.on('error', this.handleValidationError, this);
    },
    render: function() {
        // catch potential outside call before template loaded
        if (!this.template) return this;

        var listEle$ = this.$el.find('.course-advanced-policy-list');
        listEle$.empty();
        // In this case, the fieldToSelectorMap (inherited from ValidatingView) use a map
        // from the key to itself. Therefore the selectorToField map is the same object.
        this.fieldToSelectorMap = this.selectorToField = {};

        // iterate through model and produce key : value editors for each property in model.get
        var self = this;
        _.each(_.sortBy(_.keys(this.model.attributes), _.identity),
            function(key) {
                listEle$.append(self.getTemplate(key, self.model.get(key)));
                self.fieldToSelectorMap[key] = key;
            });
        var policyValues = listEle$.find('.json');
        _.each(policyValues, this.attachJSONEditor, this);
        this.showMessage();
        return this;
    },
    attachJSONEditor : function (textarea) {
        // Since we are allowing duplicate keys at the moment, it is possible that we will try to attach
        // JSON Editor to a value that already has one. Therefore only attach if no CodeMirror peer exists.
        if ( $(textarea).siblings().hasClass('CodeMirror')) {
            return;
        }

        var self = this;
        CodeMirror.fromTextArea(textarea, {
            mode: "application/json", lineNumbers: false, lineWrapping: false,
            onChange: function() {
                self.showSaveCancelButtons();
            },
            onBlur: function (mirror) {
                var key = $(mirror.getWrapperElement()).closest('.field-group').children('.key').attr('id');
                var stringValue = $.trim(mirror.getValue());
                // update CodeMirror to show the trimmed value.
                mirror.setValue(stringValue);
                var JSONValue = undefined;
                try {
                    JSONValue = JSON.parse(stringValue);
                } catch (e) {
                    // If it didn't parse, try converting non-arrays/non-objects to a String.
                    // But don't convert single-quote strings, which are most likely errors.
                    var firstNonWhite = stringValue.substring(0, 1);
                    if (firstNonWhite !== "{" && firstNonWhite !== "[" && firstNonWhite !== "'") {
                        try {
                            stringValue = '"'+stringValue +'"';
                            JSONValue = JSON.parse(stringValue);
                            mirror.setValue(stringValue);
                        } catch(quotedE) {
                            // TODO: validation error
                            console.log("Error with JSON, even after converting to String.");
                            console.log(quotedE);
                            JSONValue = undefined;
                        }
                    }
                    else {
                        // TODO: validation error
                        console.log("Error with JSON, but will not convert to String.");
                        console.log(e);
                    }
                }
                if (JSONValue !== undefined) {
                    // Is it OK to clear all validation errors? If we don't we get problems with errors overlaying.
                    self.clearValidationErrors();
                    self.model.set(key, JSONValue, {validate: true});
                }
            }
        });
    },

    showMessage: function (type) {
        this.$el.find(".message-status").removeClass("is-shown");
        if (type) {
            if (type === this.error_saving) {
                this.$el.find(".message-status.error").addClass("is-shown");
            }
            else if (type === this.successful_changes) {
                this.$el.find(".message-status.confirm").addClass("is-shown");
                this.hideSaveCancelButtons();
            }
        }
        else {
            // This is the case of the page first rendering, or when Cancel is pressed.
            this.hideSaveCancelButtons();
            this.toggleNewButton(true);
        }
    },

    showSaveCancelButtons: function() {
       if (!this.buttonsVisible) {
           this.$el.find(".message-status").removeClass("is-shown");
           $('.wrapper-notification').addClass('is-shown');
           this.buttonsVisible = true;
       }
    },

    hideSaveCancelButtons: function() {
        $('.wrapper-notification').removeClass('is-shown');
        this.buttonsVisible = false;
    },

    toggleNewButton: function (enable) {
        var newButton = this.$el.find(".new-button");
        if (enable) {
            newButton.removeClass('disabled');
        }
        else {
            newButton.addClass('disabled');
        }
    },

    deleteEntry : function(event) {
        event.preventDefault();
        // find out which entry
        var li$ = $(event.currentTarget).closest('li');
        // Not data b/c the validation view uses it for a selector
        var key = $('.key', li$).attr('id');

        delete this.fieldToSelectorMap[key];
        if (key !== this.model.new_key) {
            this.model.deleteKeys.push(key);
            this.model.unset(key);
        }
        li$.remove();
        this.showSaveCancelButtons();
    },
    saveView : function(event) {
        // TODO one last verification scan:
        //    call validateKey on each to ensure proper format
        //    check for dupes
        var self = event.data;
        self.model.save({},
            {
            success : function() {
                self.render();
                self.showMessage(self.successful_changes);
            },
            error : CMS.ServerError
        });
    },
    revertView : function(event) {
        var self = event.data;
        self.model.deleteKeys = [];
        self.model.clear({silent : true});
        self.model.fetch({
            success : function() { self.render(); },
            error : CMS.ServerError
        });
    },
    addEntry : function() {
        var listEle$ = this.$el.find('.course-advanced-policy-list');
        var newEle = this.getTemplate("", "");
        listEle$.append(newEle);
        this.fieldToSelectorMap[this.model.new_key] = this.model.new_key;
        // need to re-find b/c replaceWith seems to copy rather than use the specific ele instance
        var policyValueDivs = this.$el.find('#' + this.model.new_key).closest('li').find('.json');
        // only 1 but hey, let's take advantage of the context mechanism
        _.each(policyValueDivs, this.attachJSONEditor, this);
        this.toggleNewButton(false);
        this.showSaveCancelButtons();
    },
    updateKey : function(event) {
        var parentElement = $(event.currentTarget).closest('.key');
        // old key: either the key as in the model or new_key.
        // That is, it doesn't change as the val changes until val is accepted.
        var oldKey = parentElement.attr('id');
        // TODO: validation of keys with spaces. For now at least trim strings to remove initial and
        // trailing whitespace
        var newKey = $.trim($(event.currentTarget).val());
        if (oldKey !== newKey) {
            // TODO: is it OK to erase other validation messages?
            this.clearValidationErrors();

            if (!this.validateKey(oldKey, newKey)) return;

//  TODO: re-enable validation
//            if (this.model.has(newKey)) {
//                var error = {};
//                error[oldKey] = 'You have already defined "' + newKey + '" in the manual policy definitions.';
//                error[newKey] = "You tried to enter a duplicate of this key.";
//                this.model.trigger("error", this.model, error);
//                return false;
//            }

            // explicitly call validate to determine whether to proceed (relying on triggered error means putting continuation in the success
            // method which is uglier I think?)
            var newEntryModel = {};
            // set the new key's value to the old one's
            newEntryModel[newKey] = (oldKey === this.model.new_key ? '' : this.model.get(oldKey));

            var validation = this.model.validate(newEntryModel);
            if (validation) {
                if (_.has(validation, newKey)) {
                    // swap to the key which the map knows about
                    validation[oldKey] = validation[newKey];
                }
                this.model.trigger("error", this.model, validation);
                // abandon update
                return;
            }

            // Now safe to actually do the update
            this.model.set(newEntryModel);

            delete this.fieldToSelectorMap[oldKey];

            if (oldKey !== this.model.new_key) {
                // mark the old key for deletion and delete from field maps
                this.model.deleteKeys.push(oldKey);
                this.model.unset(oldKey) ;
            }
            else {
                // id for the new entry will now be the key value. Enable new entry button.
                this.toggleNewButton(true);
            }
            
            // check for newkey being the name of one which was previously deleted in this session
            var wasDeleting = this.model.deleteKeys.indexOf(newKey);
            if (wasDeleting >= 0) {
                this.model.deleteKeys.splice(wasDeleting, 1);
            }

            // Update the ID to the new value.
            parentElement.attr('id', newKey);
            
            this.fieldToSelectorMap[newKey] = newKey;
        }
    },
    validateKey : function(oldKey, newKey) {
        // model validation can't handle malformed keys nor notice if 2 fields have same key; so, need to add that chk here
        // TODO ensure there's no spaces or illegal chars (note some checking for spaces currently done in model's
        // validate method.
//        if (_.isEmpty(newKey)) {
//            var error = {};
//            error[oldKey] = "Key cannot be an empty string";
//            this.model.trigger("error", this.model, error);
//            return false;
//        }
//        else return true;
        return true;
    },

    getTemplate: function (key, value) {
        return this.template({ key : key, value : JSON.stringify(value, null, 4),
            keyUniqueId: _.uniqueId('policy_key_'), valueUniqueId: _.uniqueId('policy_value_')});
    }
});