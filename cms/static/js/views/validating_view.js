CMS.Views.ValidatingView = Backbone.View.extend({
    // Intended as an abstract class which catches validation errors on the model and 
    // decorates the fields. Needs wiring per class, but this initialization shows how 
    // either have your init call this one or copy the contents
    initialize : function() {
        this.model.on('error', this.handleValidationError, this);
        this.selectorToField = _.invert(this.fieldToSelectorMap);
    },

    errorTemplate : _.template('<span class="message-error"><%= message %></span>'),

    events : {
        "blur input" : "clearValidationErrors",
        "blur textarea" : "clearValidationErrors"
    },
    fieldToSelectorMap : {
        // Your subclass must populate this w/ all of the model keys and dom selectors 
        // which may be the subjects of validation errors
    },
    _cacheValidationErrors : [],
    handleValidationError : function(model, error) {
        // error triggered either by validation or server error
        // error is object w/ fields and error strings
        for (var field in error) {
            var ele = this.$el.find('#' + this.fieldToSelectorMap[field]);
            if (ele.length === 0) {
                // check if it might a server error: note a typo in the field name 
                // or failure to put in a map may cause this to muffle validation errors
                if (_.has(error, 'error') && _.has(error, 'responseText')) {
                    CMS.ServerError(model, error);
                    return;
                }
                else continue;
            }
            this._cacheValidationErrors.push(ele);
            if ($(ele).is('div')) {
                // put error on the contained inputs
                $(ele).find('input, textarea').addClass('error');
            }
            else $(ele).addClass('error');
            $(ele).parent().append(this.errorTemplate({message : error[field]}));
        }
    },

    clearValidationErrors : function() {
        // error is object w/ fields and error strings
        while (this._cacheValidationErrors.length > 0) {
            var ele = this._cacheValidationErrors.pop(); 
            if ($(ele).is('div')) {
                // put error on the contained inputs
                $(ele).find('input, textarea').removeClass('error');
            }
            else $(ele).removeClass('error');
            $(ele).nextAll('.message-error').remove();
        }
    },

    saveIfChanged : function(event) {
        // returns true if the value changed and was thus sent to server
        var field = this.selectorToField[event.currentTarget.id];
        var currentVal = this.model.get(field);
        var newVal = $(event.currentTarget).val();
        this.clearValidationErrors(); // curr = new if user reverts manually
        if (currentVal != newVal) {
            this.model.save(field, newVal);
            return true;
        }
        else return false;
    },
    // these should perhaps go into a superclass but lack of event hash inheritance demotivates me
    inputFocus : function(event) {
        $("label[for='" + event.currentTarget.id + "']").addClass("is-focused");
    },
    inputUnfocus : function(event) {
        $("label[for='" + event.currentTarget.id + "']").removeClass("is-focused");
    }
});
