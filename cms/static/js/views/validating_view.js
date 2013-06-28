CMS.Views.ValidatingView = Backbone.View.extend({
    // Intended as an abstract class which catches validation errors on the model and
    // decorates the fields. Needs wiring per class, but this initialization shows how
    // either have your init call this one or copy the contents
    initialize : function() {
        this.listenTo(this.model, 'invalid', this.handleValidationError);
        this.selectorToField = _.invert(this.fieldToSelectorMap);
    },

    errorTemplate : _.template('<span class="message-error"><%= message %></span>'),

    save_message: gettext("Your changes will not take effect until you save your progress."),

    events : {
        "change input" : "clearValidationErrors",
        "change textarea" : "clearValidationErrors"
    },
    fieldToSelectorMap : {
        // Your subclass must populate this w/ all of the model keys and dom selectors
        // which may be the subjects of validation errors
    },
    _cacheValidationErrors : [],

    handleValidationError : function(model, error) {
        // error is object w/ fields and error strings
        for (var field in error) {
            var ele = this.$el.find('#' + this.fieldToSelectorMap[field]);
            this._cacheValidationErrors.push(ele);
            this.getInputElements(ele).addClass('error');
            $(ele).parent().append(this.errorTemplate({message : error[field]}));
        }
    },

    clearValidationErrors : function() {
        // error is object w/ fields and error strings
        while (this._cacheValidationErrors.length > 0) {
            var ele = this._cacheValidationErrors.pop();
            this.getInputElements(ele).removeClass('error');
            $(ele).nextAll('.message-error').remove();
        }
    },

    setField : function(event) {
        // Set model field and return the new value.
        this.clearValidationErrors();
        var field = this.selectorToField[event.currentTarget.id];
        var newVal = $(event.currentTarget).val();
        this.model.set(field, newVal, {validate: true});
        return newVal;
    },
    // these should perhaps go into a superclass but lack of event hash inheritance demotivates me
    inputFocus : function(event) {
        $("label[for='" + event.currentTarget.id + "']").addClass("is-focused");
    },
    inputUnfocus : function(event) {
        $("label[for='" + event.currentTarget.id + "']").removeClass("is-focused");
    },

    getInputElements: function(ele) {
        var inputElements = 'input, textarea';
        if ($(ele).is(inputElements)) {
            return $(ele);
        }
        else {
            // put error on the contained inputs
            return $(ele).find(inputElements);
        }
    },

    showNotificationBar: function(message, primaryClick, secondaryClick) {
        if(this.notificationBarShowing) {
            return;
        }
        var self = this;
        this.confirmation = new CMS.Views.Notification.Warning({
            title: gettext("You've made some changes"),
            message: message,
            actions: {
                primary: {
                    "text": gettext("Save Changes"),
                    "class": "action-save",
                    "click": function() {
                        primaryClick();
                        self.confirmation.hide();
                        self.notificationBarShowing = false;
                    }
                },
                secondary: [{
                    "text": gettext("Cancel"),
                    "class": "action-cancel",
                    "click": function() {
                        if(secondaryClick) {
                            secondaryClick();
                        }
                        self.model.clear({silent : true});
                        /*self.model.fetch({
                            success : function() { self.render(); },
                            reset: true
                        });*/
                        self.confirmation.hide();
                        self.notificationBarShowing = false;
                    }
                }]
            }});
        this.notificationBarShowing = true;
        this.confirmation.show();
    },

    showSavedBar: function(title, message) {
        var defaultTitle = gettext('Your changes have been saved.');
        this.saved = new CMS.Views.Alert.Confirmation({
            title: title || defaultTitle,
            message: message,
            closeIcon: false
        });
        this.saved.show();
    },

    saveView: function() {
        var self = this;
        this.model.save({},
                        {success: function() {
                            self.showSavedBar();
                        }});
    }
});
