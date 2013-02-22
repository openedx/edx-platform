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
        // keypress to catch alpha keys and backspace/delete on some browsers
        'keypress .policy-key' : "showSaveCancelButtons",
        // keyup to catch backspace/delete reliably
        'keyup .policy-key' : "showSaveCancelButtons",
        'focus :input' : "focusInput",
        'blur :input' : "blurInput"
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
        // because these are outside of this.$el, they can't be in the event hash
        $('.save-button').on('click', this, this.saveView);
        $('.cancel-button').on('click', this, this.revertView);
        this.model.on('error', this.handleValidationError, this);
    },
    render: function() {
        // catch potential outside call before template loaded
        if (!this.template) return this;

        var listEle$ = this.$el.find('.course-advanced-policy-list');
        listEle$.empty();
        
        // b/c we've deleted all old fields, clear the map and repopulate
        this.fieldToSelectorMap = {};
        this.selectorToField = {};

        // iterate through model and produce key : value editors for each property in model.get
        var self = this;
        _.each(_.sortBy(_.keys(this.model.attributes), _.identity),
            function(key) {
                listEle$.append(self.renderTemplate(key, self.model.get(key)));
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
        var oldValue = $(textarea).val();
        CodeMirror.fromTextArea(textarea, {
            mode: "application/json", lineNumbers: false, lineWrapping: false,
            onChange: function(instance, changeobj) {
                // this event's being called even when there's no change :-(
                if (instance.getValue() !== oldValue) self.showSaveCancelButtons();
            },
            onFocus : function(mirror) {
              $(textarea).parent().children('label').addClass("is-focused");
            },
            onBlur: function (mirror) {
                $(textarea).parent().children('label').removeClass("is-focused");
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

    showSaveCancelButtons: function(event) {
        if (!this.buttonsVisible) {
            if (event && (event.type === 'keypress' || event.type === 'keyup')) {
                // check whether it's really an altering event: note, String.fromCharCode(keyCode) will 
                // give positive values for control/command/option-letter combos; so, don't use it
                if (!((event.charCode && String.fromCharCode(event.charCode) !== "") ||
                        // 8 = backspace, 46 = delete
                        event.keyCode === 8 || event.keyCode === 46)) return;
            }
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

        delete this.selectorToField[this.fieldToSelectorMap[key]];
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
        var newEle = this.renderTemplate("", "");
        listEle$.append(newEle);
        // need to re-find b/c replaceWith seems to copy rather than use the specific ele instance
        var policyValueDivs = this.$el.find('#' + this.model.new_key).closest('li').find('.json');
        // only 1 but hey, let's take advantage of the context mechanism
        _.each(policyValueDivs, this.attachJSONEditor, this);
        this.toggleNewButton(false);
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

            if (this.model.has(newKey)) {
                var error = {};
                error[oldKey] = 'You have already defined "' + newKey + '" in the manual policy definitions.';
                error[newKey] = "You tried to enter a duplicate of this key.";
                this.model.trigger("error", this.model, error);
                return false;
            }

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

            // update maps
            var selector = this.fieldToSelectorMap[oldKey];
            this.selectorToField[selector] = newKey;
            this.fieldToSelectorMap[newKey] = selector;
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
            
        }
    },
    validateKey : function(oldKey, newKey) {
        // model validation can't handle malformed keys nor notice if 2 fields have same key; so, need to add that chk here
        // TODO ensure there's no spaces or illegal chars (note some checking for spaces currently done in model's
        // validate method.
        return true;
    },

    renderTemplate: function (key, value) {
        var newKeyId = _.uniqueId('policy_key_'),
        newEle = this.template({ key : key, value : JSON.stringify(value, null, 4),
            keyUniqueId: newKeyId, valueUniqueId: _.uniqueId('policy_value_')});
        
        this.fieldToSelectorMap[(_.isEmpty(key) ? this.model.new_key : key)] = newKeyId;
        this.selectorToField[newKeyId] = (_.isEmpty(key) ? this.model.new_key : key);
        return newEle;
    },
    
    focusInput : function(event) {
        $(event.target).prev().addClass("is-focused");
    },
    blurInput : function(event) {
        $(event.target).prev().removeClass("is-focused");
    }
});