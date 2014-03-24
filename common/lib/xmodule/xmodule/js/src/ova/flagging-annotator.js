var _ref,
  __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
  __hasProp = {}.hasOwnProperty,
  __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

Annotator.Plugin.Flagging = (function(_super) {
	__extends(Flagging, _super);
	
	//If you do not have options, delete next line and the parameters in the declaration function
    Flagging.prototype.options = null;
	
    //declaration function, remember to set up submit and/or update as necessary, if you don't have
    //options, delete the options line below.
	function Flagging(element,options) {
		this.updateViewer = __bind(this.updateViewer, this);
        this.flagAnnotation = __bind(this.flagAnnotation, this);
        this.unflagAnnotation = __bind(this.unflagAnnotation, this);
        this.options = options;
		_ref = Flagging.__super__.constructor.apply(this, arguments);
		return _ref;
	}
	
    //example variables to be used to receive input in the annotator view
	Flagging.prototype.field = null;
	Flagging.prototype.input = null;
    Flagging.prototype.hasPressed = false;
    
    //this function will initialize the plug in. Create your fields here in the editor and viewer.
    Flagging.prototype.pluginInit = function() {
		console.log("Flagging-pluginInit");
		//Check that annotator is working
		if (!Annotator.supported()) {
			return;
		}
		
		
		//-- Viewer
		var newview = this.annotator.viewer.addField({
			load: this.updateViewer,
		});
        
        

		return this.input = $(this.field).find(':input');
	};
    
    
    //The following allows you to edit the annotation popup when the viewer has already
    //hit submit and is just viewing the annotation.
	Flagging.prototype.updateViewer = function(field, annotation) {
        $(field).remove();//remove the empty div created by annotator
		var self = this;
        this.hasPressed = false;
        //perform routine to check if user has pressed the button before
        var tags = typeof annotation.tags != 'undefined'?annotation.tags:[];
        var user = this.annotator.plugins.Permissions.user.id;
        tags.forEach(function(t){
            if (t.indexOf("flagged")>=0) {
                var usertest = t.replace('flagged-','');
                if (usertest == user) 
                    self.hasPressed = true;
                
            }
        });
        var fieldControl = $(this.annotator.viewer.element.find('.annotator-controls')).parent();
        if (this.hasPressed) {
			fieldControl.prepend('<button title="You have already reported this annotation." class="flag-icon-used">');
            var flagEl = fieldControl.find('.flag-icon-used'),
                self = this;
            flagEl.click(function(){self.unflagAnnotation(annotation,user,flagEl,field)});
        } else{
            fieldControl.prepend('<button title="Report annotation as inappropriate or offensive." class="flag-icon">');
            var flagEl = fieldControl.find('.flag-icon'),
                self = this;
            flagEl.click(function(){self.flagAnnotation(annotation,user,flagEl,field)});
            
        }
    }
    
    Flagging.prototype.flagAnnotation = function(annotation, userId, flagElement, field) {
        flagElement.attr("class","flag-icon-used");
        flagElement.attr("title","You have already reported this annotation.");
        if (typeof annotation.tags == 'undefined') {
            annotation.tags = ['flagged-'+userId];
        } else{
            annotation.tags.push("flagged-"+userId);
        }
        this.annotator.plugins['Store'].annotationUpdated(annotation);
        this.annotator.publish("flaggedAnnotation",[field,annotation]);
        
    }
    
    Flagging.prototype.unflagAnnotation = function(annotation, userId, flagElement, field) {
        flagElement.attr("class", "flag-icon");
        flagElement.attr("title","Report annotation as inappropriate or offensive.");
        annotation.tags.splice(annotation.tags.indexOf('flagged-'+userId));
        this.annotator.plugins['Store'].annotationUpdated(annotation);
        this.annotator.publish("flaggedAnnotation",[field,annotation]);
    }
    
    return Flagging;

})(Annotator.Plugin);
