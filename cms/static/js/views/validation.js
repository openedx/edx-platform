define(["js/views/baseview", "underscore", "jquery", "gettext", "common/js/components/views/feedback_notification", "common/js/components/views/feedback_alert", "js/views/baseview", "jquery.smoothScroll"],
    function(BaseView, _, $, gettext, NotificationView, AlertView) {

var ValidatingView = BaseView.extend({
    // Intended as an abstract class which catches validation errors on the model and
    // decorates the fields. Needs wiring per class, but this initialization shows how
    // either have your init call this one or copy the contents
    initialize : function() {
        this.listenTo(this.model, 'invalid', this.handleValidationError);
        this.selectorToField = _.invert(this.fieldToSelectorMap);
    },

    errorTemplate : _.template('<span class="message-error"><%= message %></span>'),

    save_title: gettext("You've made some changes"),
    save_message: gettext("Your changes will not take effect until you save your progress."),
    error_title: gettext("You've made some changes, but there are some errors"),
    error_message: gettext("Please address the errors on this page first, and then save your progress."),

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
        this.clearValidationErrors();
        // error is object w/ fields and error strings
        for (var field in error) {
            var ele = this.$el.find('#' + this.fieldToSelectorMap[field]);
            this._cacheValidationErrors.push(ele);
            this.getInputElements(ele).addClass('error');
            $(ele).parent().append(this.errorTemplate({message : error[field]}));
        }
        $('.wrapper-notification-warning').addClass('wrapper-notification-warning-w-errors');
        $('.action-save').addClass('is-disabled');
        // TODO: (pfogg) should this text fade in/out on change?
        $('#notification-warning-title').text(this.error_title);
        $('#notification-warning-description').text(this.error_message);
    },

    clearValidationErrors : function() {
        // error is object w/ fields and error strings
        while (this._cacheValidationErrors.length > 0) {
            var ele = this._cacheValidationErrors.pop();
            this.getInputElements(ele).removeClass('error');
            $(ele).nextAll('.message-error').remove();
        }
        $('.wrapper-notification-warning').removeClass('wrapper-notification-warning-w-errors');
        $('.action-save').removeClass('is-disabled');
        $('#notification-warning-title').text(this.save_title);
        $('#notification-warning-description').text(this.save_message);
    },

    setField : function(event) {
        // Set model field and return the new value.
        this.clearValidationErrors();
        var field = this.selectorToField[event.currentTarget.id];
        var newVal = ''
        if(event.currentTarget.type == 'checkbox'){
            newVal = $(event.currentTarget).is(":checked").toString();
        }else{
            newVal = $(event.currentTarget).val();
        }
        this.model.set(field, newVal);
        this.model.isValid();
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
        // Show a notification with message. primaryClick is called on
        // pressing the save button, and secondaryClick (if it's
        // passed, which it may not be) will be called on
        // cancel. Takes care of hiding the notification bar at the
        // appropriate times.
        if(this.notificationBarShowing) {
            return;
        }
        // If we've already saved something, hide the alert.
        if(this.saved) {
            this.saved.hide();
        }
        var self = this;
        this.confirmation = new NotificationView.Warning({
            title: this.save_title,
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
                        self.confirmation.hide();
                        self.notificationBarShowing = false;
                    }
                }]
            }});
        this.notificationBarShowing = true;
        this.confirmation.show();
        // Make sure the bar is in the right state
        this.model.isValid();
    },

    showSavedBar: function(title, message) {
        var defaultTitle = gettext('Your changes have been saved.');
        this.saved = new AlertView.Confirmation({
            title: title || defaultTitle,
            message: message,
            closeIcon: false
        });
        this.saved.show();
        $.smoothScroll({
            offset: 0,
            easing: 'swing',
            speed: 1000
        });
    },

    saveView: function() {
        var self = this;
        this.model.save(
            {},
            {
                success: function() {
                    self.showSavedBar();
                    self.render();
                },
                silent: true
            }
        );
    }
});

return ValidatingView;

}); // end define()
