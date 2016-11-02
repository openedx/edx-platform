var _ref,
  __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
  __hasProp = {}.hasOwnProperty,
  __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

Annotator.Plugin.Flagging = (function(_super) {
    __extends(Flagging, _super);
    
    Flagging.prototype.options = null;
    
    // declaration function, remember to set up submit and/or update as necessary, if you don't have
    // options, delete the options line below.
    function Flagging(element,options) {
        this.updateViewer = __bind(this.updateViewer, this);
        this.updateField = __bind(this.updateField, this);
        this.submitField = __bind(this.submitField, this);
        this.flagAnnotation = __bind(this.flagAnnotation, this);
        this.unflagAnnotation = __bind(this.unflagAnnotation, this);
        this.getTotalFlaggingTags = __bind(this.getTotalFlaggingTags, this);
        this.options = options;
        _ref = Flagging.__super__.constructor.apply(this, arguments);
        return _ref;
    }
    
    // variables to be used to receive input in the annotator view
    Flagging.prototype.field = null;
    Flagging.prototype.input = null;
    Flagging.prototype.hasPressed = false;
    Flagging.prototype.activeAnnotation = null;
    Flagging.prototype.mixedTags = null;
    
    // this function will initialize the plug-in
    Flagging.prototype.pluginInit = function() {
        console.log("Flagging-pluginInit");
        
        // Check that annotator is working
        if (!Annotator.supported()) {
            return;
        }
        
        // -- Editor
        //creates a checkbox to remove all flags
        var self = this;
        this.field = this.annotator.editor.addField({
            type: 'checkbox',
            load: this.updateField,
            // Translators: please note that this is not a literal flag, but rather a report
            label: Annotator._t(gettext('Check the box to remove all flags.')),
            submit: this.submitField,
        });
        
        // -- Viewer
        var newview = this.annotator.viewer.addField({
            load: this.updateViewer,
        });

        return this.input = $(this.field).find(':input');
    };
    
    /**
     * Gets the total number of tags associated with the flagging tool.
     * @param {Object} annotation Annotation item from Annotator.
     */
    Flagging.prototype.getTotalFlaggingTags = function(annotation){
        var tags = (typeof annotation.tags !== 'undefined') ? annotation.tags.slice() : [];
        // Goes through and gets the number of tags that contained the keyword "flagged"
        return $.grep(tags, function(tag, index){
            return (tag.indexOf('flagged') !== -1);
        }).length;
    }
    
    /**
     * Creates a new field in the editor in order to delete the flagged tags.
     * @param {HTMLElement} field The HTML element contained in the editor reserved for flagging.
     * @param {Object} annotation Annotation item from Annotator.
     */
    Flagging.prototype.updateField = function(field, annotation) {
        
        // figure out whether annotation is of type image or if ova is not defined (meaning it
        // it doesn't have a type yet, but it is still an image).
        var user_email = (annotation.media === "image" || typeof ova === 'undefined') ? 
                            osda.options.optionsAnnotator.permissions.user.id:
                            ova.options.optionsAnnotator.permissions.user.id;
        
        // get total number of flag tags as well as save a copy of the mixed tags
        var totalFlags = this.getTotalFlaggingTags(annotation);   
        this.mixedTags = annotation.tags;     
        var self = this;
        
        // only show this field if you are an instructor and there are flags to remove
        if(Catch.options.instructor_email === user_email && totalFlags > 0){
            // Translators: 'totalFlags' is the number of flags solely for that annotation
            var message = ngettext("Check the box to remove %(totalFlags)s flag.", "Check the box to remove %(totalFlags)s flags.", totalFlags);
            $(field).find('label')[0].innerHTML = interpolate(message, {totalFlags : totalFlags}, true);
            this.activeAnnotation = annotation;
            
            // add function to change the text when the user checks the box or removes the check
            $(field).find('input').change(function(evt){
                if(!$(field).find('input:checkbox:checked').val()){
                    var count = self.getTotalFlaggingTags(self.activeAnnotation);
                    // Translators: 'count' is the number of flags solely for that annotation that will be removed
                    var message = ngettext("Check the box to remove %(count)s flag.", "Check the box to remove %(count)s flags.", count)
                    $(field).find('label')[0].innerHTML = interpolate(message, {count: count}, true);
                } else {
                    $(field).find('label')[0].innerHTML = gettext("All flags have been removed. To undo, uncheck the box.");
                }
            });
            $(field).show();
        } else {
            $(field).hide();
        }
    }
    
    /**
     * Makes last-minute changes to the annotation right before it is saved in the server.
     * @param {HTMLElement} field The HTML element contained in the editor reserved for flagging.
     * @param {Object} annotation Annotation item from Annotator.     
     */
    Flagging.prototype.submitField = function(field, annotation) {
        // if the user did not check the box go back and input all of the tags. 
        if (!$(field).find('input:checkbox:checked').val()){
            annotation.tags = this.mixedTags;
        }
    }
    
    /** 
     * The following allows you to edit the annotation popup when the viewer has already
     * hit submit and is just viewing the annotation.
     * @param {HTMLElement} field The HTML element contained in the editor reserved for flagging.
     * @param {Object} annotation Annotation item from Annotator.
     */
    Flagging.prototype.updateViewer = function(field, annotation) {
        var self = this;
        this.hasPressed = false;
        
        // perform routine to check if user has pressed the button before
        var tags = typeof annotation.tags != 'undefined'?annotation.tags:[];
        var user = this.annotator.plugins.Permissions.user.id;
        tags.forEach(function(t){
            if (t.indexOf("flagged")>=0) {
                var usertest = t.replace('flagged-','');
                if (usertest == user) 
                    self.hasPressed = true;
                
            }
        });

        // changes display based on check done above
        var fieldControl = $(this.annotator.viewer.element.find('.annotator-controls')).parent();
        if (this.hasPressed) {

            // make sure to use id when searching for the item so that only one of them gets changed
            var message = gettext("You have already reported this annotation.");
            fieldControl.prepend('<button title="' + message + '" class="flag-icon-used" id="' + annotation.id + '">');
            
            var flagEl = fieldControl.find('.flag-icon-used#' + annotation.id);
            var self = this;
            
            // sets function to unflag after next click
            flagEl.click(function(){self.unflagAnnotation(annotation,user,flagEl,field)});
        
        } else{
            
            // likewise, make sure to use id when searching for the item so that only one is changed
            var message = gettext("Report annotation as inappropriate or offensive.");
            fieldControl.prepend('<button title="' + message + '" class="flag-icon" id="' + annotation.id + '">');
            
            var flagEl = fieldControl.find('.flag-icon#' + annotation.id);
            var self = this;
            
            // sets function to flag after next click
            flagEl.click(function(){self.flagAnnotation(annotation,user,flagEl,field)});
        }
        
        var user_email = annotation.media === "image" ? 
                            osda.options.optionsAnnotator.permissions.user.id:
                            ova.options.optionsAnnotator.permissions.user.id;
        var totalFlags = this.getTotalFlaggingTags(annotation);
        
        // only show the number of times an annotation has been flagged if they are the instructors
        if(Catch.options.instructor_email === user_email && totalFlags > 0){
            // Translators: 'count' is the number of flags solely for that annotation
            var message = ngettext("This annotation has %(count)s flag.","This annotation has %(count)s flags.", totalFlags);
            $(field).append("<div class=\"flag-count\">" + interpolate(message, {count : totalFlags}, true) + "</div>");
        } else {
            $(field).remove(); // remove the empty div created by annotator
        }
    }
    
    /**
     * This function changes the visual aspects of flagging an Annotation and sends changes
     * to the database backend.
     */
    Flagging.prototype.flagAnnotation = function(annotation, userId, flagElement, field) {
        
        // changes the class and title to show user's flagging action worked
        flagElement.attr("class","flag-icon-used");
        flagElement.attr("title", gettext("You have already reported this annotation."));

        // it adds the appropriate tag with the user name to make sure it is added
        if (typeof annotation.tags == 'undefined') {
            annotation.tags = ['flagged-'+userId];
        } else{
            annotation.tags.push("flagged-"+userId);
        }

        // annotation gets updated and a warning is published that an annotation has been flagged
        this.annotator.plugins['Store'].annotationUpdated(annotation);
        this.annotator.publish("flaggedAnnotation",[field,annotation]);
        
        // now that it is flagged, it sets the click function to unflag
        flagElement.click(function(){self.unflagAnnotation(annotation,userId,flagElement,field)});
    }
    
    /**
     * This function changes the visual aspects of unflagging an Annotation and sends changes
     * to the database backend.
     */
    Flagging.prototype.unflagAnnotation = function(annotation, userId, flagElement, field) {
        
        // changes the class and title to show user's unflagging action worked
        flagElement.attr("class", "flag-icon");
        flagElement.attr("title", gettext("Report annotation as inappropriate or offensive."));
        
        // it removes the tag that signifies flagging
        annotation.tags.splice(annotation.tags.indexOf('flagged-'+userId));
        
        // annotation gets updated without the tag and a warning is published that flagging is changed
        this.annotator.plugins['Store'].annotationUpdated(annotation);
        this.annotator.publish("flaggedAnnotation",[field,annotation]);
        
        // now that it is unflagged, it sets the click function to flag
        flagElement.click(function(){self.unflagAnnotation(annotation,userId,flagElement,field)});
    }
    
    return Flagging;

})(Annotator.Plugin);
