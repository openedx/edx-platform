if (!CMS.Views['Settings']) CMS.Views.Settings = {};

CMS.Views.Settings.Advanced = CMS.Views.ValidatingView.extend({
    // the key for a newly added policy-- before the user has entered a key value
    new_key : "__new_advanced_key__",

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
        // In this case, the fieldToSelectorMap (inherited from ValidatingView) use a map
        // from the key to itself. Therefore the selectorToField map is the same object.
        this.fieldToSelectorMap = this.selectorToField = {};

        // iterate through model and produce key : value editors for each property in model.get
        var self = this;
        _.each(_.sortBy(_.keys(this.model.attributes), _.identity),
            function(key) {
                // TODO: working here
                var newEl = self.template({ key : key, value : self.model.get(key)});
                listEle$.append(newEl);

                self.fieldToSelectorMap[key] = key;

                //        var editor = ace.edit('course-advanced-policy-1-value');
                //        editor.setTheme("ace/theme/chrome");
                //        editor.getSession().setMode("ace/mode/json");

            });
        return this;
    },
    deleteEntry : function(event) {
        event.preventDefault();
        // find out which entry
        var li$ = $(event.currentTarget).closest('li');
        // Not data b/c the validation view uses it for a selector
        var key = $('.key', li$).attr('id');

        delete this.fieldToSelectorMap[key];
        if (key !== this.new_key) {
            this.model.deleteKeys.push(key);
            this.model.unset(key);
        }
        li$.remove();
    },
    saveView : function(event) {
        // TODO one last verification scan:
        //    call validateKey on each to ensure proper format
        //    check for dupes
        var self = this;
        this.model.save({},
            {
            success : function() {
                self.render();
                window.alert("Saved");
            },
            error : CMS.ServerError
        });
    },
    revertView : function(event) {
        this.model.deleteKeys = [];
        var self = this;
        this.model.clear({silent : true});
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
        this.fieldToSelectorMap[this.new_key] = this.new_key;
    },
    updateKey : function(event) {
        // old key: either the key as in the model or new_key.
        // That is, it doesn't change as the val changes until val is accepted.
        var oldKey = $(event.currentTarget).closest('.key').attr('id');
        var newKey = $(event.currentTarget).val();
        console.log('update ', oldKey, newKey); // TODO: REMOVE ME
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
            newEntryModel[newKey] = (oldKey === this.new_key ? '' : this.model.get(oldKey));

            var validation = this.model.validate(newEntryModel);
            if (validation) {
                console.log('reserved key');
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

            if (oldKey !== this.new_key) {
                // mark the old key for deletion and delete from field maps
                this.model.deleteKeys.push(oldKey);
                this.model.unset(oldKey) ;
            }
            else {
                // enable the value entry
                this.$el.find('.course-advanced-policy-value').removeClass('disabled');
            }
            
            // check for newkey being the name of one which was previously deleted in this session
            var wasDeleting = this.model.deleteKeys.indexOf(newKey);
            if (wasDeleting >= 0) {
                this.model.deleteKeys.splice(wasDeleting, 1);
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