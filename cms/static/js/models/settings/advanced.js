if (!CMS.Models['Settings']) CMS.Models.Settings = {};

CMS.Models.Settings.Advanced = Backbone.Model.extend({
    defaults: {
        // the properties are whatever the user types in
    },
    // which keys to send as the deleted keys on next save
    deleteKeys : [],
    blacklistKeys : [], // an array which the controller should populate directly for now [static not instance based]
    initialize: function() {
        console.log('in initialize');
    },
    validate: function(attrs) {
        var errors = {};
        for (key in attrs) {
            if (_.contains(this.blacklistKeys, key)) {
                errors[key] = key + " is a reserved keyword or has another editor";
            }
        }
        if (!_.isEmpty(errors)) return errors;
    }
});

if (!CMS.Views['Settings']) CMS.Views.Settings = {};

CMS.Views.Settings.Advanced = CMS.Views.ValidatingView.extend({
    // Model class is CMS.Models.Settings.Advanced
    events : {
        'click .delete-button' : "deleteEntry",
        'click .save-button' : "saveView",
        'click .cancel-button' : "revertView",
        'click .new-button' : "addEntry",
        // update model on changes
        'change #course-advanced-policy-key' : "updateKey",
        'change #course-advanced-policy-value' : "updateValue"
        // TODO enable/disable save (add disabled class) based on validation & dirty
        // TODO enable/disable new button? 
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
        this.model.on('error', this.handleValidationError, this);
    },
    render: function() {
        // catch potential outside call before template loaded
        if (!this.template) return this;
        
        var listEle$ = this.$el.find('.course-advanced-policy-list');
        listEle$.empty();
        // same object so manipulations to one keep the other up to date
        this.fieldToSelectorMap = this.selectorToField = {};
        
        // iterate through model and produce key : value editors for each property in model.get
        var self = this;
        _.each(this.model.attributes, 
                function(value, key) {
                    listEle$.append(self.template({ key : key, value : value}));
                    self.fieldToSelectorMap[key] = key;
        });
        
        // insert the empty one
        this.addEntry();
        // Should this be on an event rather than render?
//        var editor = ace.edit('course-advanced-policy-1-value');
//        editor.setTheme("ace/theme/monokai");
//        editor.getSession().setMode("ace/mode/javascript");

        return this;
    },
    deleteEntry : function(event) {
        event.preventDefault();
        // find out which entry
        var li$ = $(event.currentTarget).closest('li');
        // Not data b/c the validation view uses it for a selector
        var key = $('.key', li$).attr('id');

        delete this.fieldToSelectorMap[key];
        if (key !== '__new_advanced_key__') {
            this.model.deleteKeys.push(key);
            delete this.model[key];
        }
        li$.remove();
    },
    saveView : function(event) {
        // TODO one last verification scan: 
        //    call validateKey on each to ensure proper format
        //    check for dupes
        
        this.model.save({
            success : function() { window.alert("Saved"); },
            error : CMS.ServerError
        });
        // FIXME don't delete if the validation didn't succeed in the save call
        // remove deleted attrs
        if (!_.isEmpty(this.model.deleteKeys)) {
            var self = this;
            // hmmm, not sure how to do this via backbone since we're not destroying the model
            $.ajax({
                url : this.model.url,
                // json to and fro
                contentType : "application/json",
                dataType : "json",
                // delete
                type : 'DELETE',
                // data
                data : JSON.stringify({ deleteKeys : this.model.deleteKeys})
            })
            .fail(function(hdr, status, error) { CMS.ServerError(self.model, "Deleting keys:" + status); })
            .done(function(data, status, error) {
                // clear deleteKeys on success
                self.model.deleteKeys = [];
            });
        }
    },
    revertView : function(event) {
        this.model.deleteKeys = [];
        var self = this;
        this.model.fetch({
            success : function() { self.render(); },
            error : CMS.ServerError
        });
    },
    addEntry : function() {
        var listEle$ = this.$el.find('.course-advanced-policy-list');
        listEle$.append(this.template({ key : "", value : ""}));
        // disable the value entry until there's an acceptable key
        listEle$.find('.course-advanced-policy-value').addClass('disabled');
        this.fieldToSelectorMap['__new_advanced_key__'] = '__new_advanced_key__';
    },
    updateKey : function(event) {
        //  old key: either the key as in the model or __new_advanced_key__. That is, it doesn't change as the val changes until val is accepted
        var oldKey = $(event.currentTarget).closest('.key').attr('id');
        var newKey = $(event.currentTarget).val();
        console.log('update ', oldKey, newKey); // REMOVE ME
        if (oldKey !== newKey) {
            // may erase other errors but difficult to just remove these
            this.clearValidationErrors();
            
            if (!this.validateKey(oldKey, newKey)) return;
            
            if (this.model.has(newKey)) {
                console.log('dupe key');
                var error = {};
                error[oldKey] = newKey + " has another entry";
                error[newKey] = "Other entry for " + newKey;
                this.model.trigger("error", this.model, error);
                return false;
            }

            // explicitly call validate to determine whether to proceed (relying on triggered error means putting continuation in the success
            // method which is uglier I think?)
            var newEntryModel = {};
            // set the new key's value to the old one's 
            newEntryModel[newKey] = (oldKey === '__new_advanced_key__' ? '' : this.model.get(oldKey));

            var validation = this.model.validate(newEntryModel); 
            if (validation) {
                console.log('reserved key');
                this.model.trigger("error", this.model, validation);
                // abandon update
                return;
            }
            
            // Now safe to actually do the update
            this.model.set(newEntryModel);
            
            delete this.fieldToSelectorMap[oldKey];
            
            if (oldKey !== '__new_advanced_key__') {
                // mark the old key for deletion and delete from field maps
                this.model.deleteKeys.push(oldKey);
                this.model.unset(oldKey) ;
            }
            else {
                // enable the value entry
                this.$el.find('.course-advanced-policy-value').removeClass('disabled');
            }
            
            // update gui (sets all the ids etc)
            $(event.currentTarget).closest('li').replaceWith(this.template({key : newKey, value : this.model.get(newKey) }));
            
            this.fieldToSelectorMap[newKey] = newKey;
        }
    },
    validateKey : function(oldKey, newKey) {
        // model validation can't handle malformed keys nor notice if 2 fields have same key; so, need to add that chk here
        // TODO ensure there's no spaces or illegal chars
        if (_.isEmpty(newKey)) {
            console.log('no key');
            var error = {};
            error[oldKey] = "Key cannot be an empty string";
            this.model.trigger("error", this.model, error);
            return false;
        }
        else return true;
    },
    updateValue : function(event) {
        // much simpler than key munging. just update the value
        var key = $(event.currentTarget).closest('.row').children('.key').attr('id');
        var value = $(event.currentTarget).val();
        console.log('updating ', key, value);
        
        this.model.set(key, value, {validate:true});
    }
});
