var _ref;
var __bind = function(fn, me) {
    return function() { 
        return fn.apply(me, arguments); 
    }; 
};
var __hasProp = {}.hasOwnProperty;
var __extends = function(child, parent) { 
    for (var key in parent) { 
        if (__hasProp.call(parent, key)) 
            child[key] = parent[key]; 
    } 
    function ctor() { 
        this.constructor = child; 
    } 
    ctor.prototype = parent.prototype; 
    child.prototype = new ctor(); 
    child.__super__ = parent.prototype; 
    return child; 
};

Annotator.Plugin.Grouping = (function(_super) {
    __extends(Grouping, _super);
    
    // this plugin will have a threshold option (-1 = plugin should be removed)
    Grouping.prototype.options = null;
    
    // sets up the grouping structure for the plug-in
    function Grouping(element, options) {
        this.pluginInit = __bind(this.pluginInit, this);
        this.reloadAnnotations = __bind(this.reloadAnnotations, this);
        this.groupAndColor = __bind(this.groupAndColor, this);
        this.clearGrouping = __bind(this.clearGrouping, this);
        this.getPos = __bind(this.getPos, this);
        this.groupingButtonPressed = __bind(this.groupingButtonPressed, this);
        this.options = options;
        _ref = Grouping.__super__.constructor.apply(this, arguments);
        return _ref;
    }
    
    // instantiation of variables to be passed around below
    Grouping.prototype.unfilteredAnnotations = null;
    Grouping.prototype.groupedAnnotations = null;
    Grouping.prototype.groupthreshold = 0;
    Grouping.prototype.useGrouping = 1;

    /**
     * Gets the current position relative to the annotation wrapper
     * @param {HTMLElement} el Element (assumed to be within annotator-wrapper) being measured.
     * @return {Object} Position of element passed in using x, y coordinates
     */
    Grouping.prototype.getPos = function(el) {
        // gets the offset of the element and wrapper
        var off = $(el).offset();
        var wrapperOff = $($('.annotator-wrapper')[0]).offset();
        
        // do height calculations from the wrapper
        return {x:off.left, y:off.top-wrapperOff.top};
    }
    
    /**
     * Initializes the plugin and its attributes.
     */
    Grouping.prototype.pluginInit = function() {
        // Check that annotator is working
        if (!Annotator.supported()) {
            console.log("Annotator is not supported");
            return;
        }
        
        // makes sure that every time a change is made to annotations, the grouping is redone
        this.annotator.subscribe('annotationsLoaded', this.reloadAnnotations);
        this.annotator.subscribe('annotationUploaded', this.reloadAnnotations);
        this.annotator.subscribe('annotationDeleted', this.reloadAnnotations);
        this.annotator.subscribe('annotationCreated', this.reloadAnnotations);
        this.annotator.subscribe('changedTabsInCatch', this.groupingButtonPressed);

        // sets up the button that toggles the grouping on or off
        var newdiv = document.createElement('div');
        var className = 'onOffGroupButton';
        newdiv.setAttribute('class', className);
        
        // if the item is in public then it should default to grouping being on
        if (options.optionsOVA.default_tab.toLowerCase() === 'public') {
            newdiv.innerHTML = "Annotation Grouping: ON";
            this.useGrouping = 1;
            // we wait for HighlightTags to complete before reloading annotations
            this.annotator.subscribe('colorizeCompleted', this.reloadAnnotations);
        } else {
            newdiv.innerHTML = "Annotation Grouping: OFF";
            $(newdiv).addClass('buttonOff');
            this.useGrouping = 0;
        }
        $($('.annotator-wrapper')[0]).prepend(newdiv);
        $(newdiv).click(this.groupingButtonPressed);
        
        // makes sure that if user resizes window, the annotations are regrouped
        var self = this;
        $(window).resize(function() {
            self.reloadAnnotations();//resize just happened, pixels changed
        });
    };
    
    /**
     * Helper function that removes all of the side buttons and sets background to yellow
     */
    Grouping.prototype.clearGrouping = function() {
        $('.groupButton').remove();
        $.each(this.unfilteredAnnotations, function(val) {
            if (val.highlights !== undefined){
                $.each(val.highlights, function(high){
                    $(high).css("background-color", "inherit");
                });
            }
        });
    }
    
    /**
     * Helper function that goes through and groups together annotations on the same line
     */
    Grouping.prototype.groupAndColor = function() {
        annotations = this.unfilteredAnnotations;
        lineAnnDict = {};
        var self = this;
        
        // for each annotation, if they have highlights, get the positions and add them
        // to a dictionary based on its initial line location
        annotations.forEach(function(annot) {
            if (annot.highlights !== undefined) {
                var loc = Math.round(self.getPos(annot.highlights[0]).y);
                if (lineAnnDict[loc] === undefined) {
                    lineAnnDict[loc] = [annot];
                    return;
                } else {
                    lineAnnDict[loc].push(annot);
                    return;
                }
            }
        });
        this.groupedAnnotations = null;
        this.groupedAnnotations = lineAnnDict;
        
        // Then it goes through and sets the color based on the threshold set
        var self = this;
        $.each(lineAnnDict, function(key, val) {
            if (val.length > self.groupthreshold) {
                val.forEach(function(anno){
                    $.each(anno.highlights, function(key, anno) {
                       $(anno).css("background-color", "inherit");   
                    });
                });
            } else {
                val.forEach(function(anno) {
                    $.each(anno.highlights, function(key, anno) {
                       $(anno).css("background-color", "rgba(255, 255, 10, .3)");   
                    });
                });
            }
        });
    }
        
    /**
     * Helper function that clears old groupings, regroups, and adds the side buttons.
     */
    Grouping.prototype.reloadAnnotations = function() {
        var annotations = this.annotator.plugins['Store'].annotations;
        // clear the sidebuttons
        this.unfilteredAnnotations = annotations;
        this.clearGrouping();   
        if (this.useGrouping === 0) {
            return;
        }
        this.groupAndColor();
        var self = this;
        
        // The following creates a sidebutton that is based on line location. it will
        // contain a number referring to the number of hidden annotations
        $.each(this.groupedAnnotations, function(key, val) {
            if (val.length > self.groupthreshold) {
                var newdiv = document.createElement('div');
                var className = 'groupButton';
                newdiv.setAttribute('class', className);
                $(newdiv).css('top', "" + key + "px");
                newdiv.innerHTML = val.length;
                $(newdiv).attr('data-selected', '0');
                $('.annotator-wrapper')[0].appendChild(newdiv);
                $(newdiv).click(function(evt){
                    if($(evt.srcElement).attr("data-selected") === '0') {
                        annotations.forEach(function(annot){
                            $.each(annot.highlights, function(key, ann) {
                                $(ann).css("background-color", "inherit");
                            });
                        });
                        self.groupedAnnotations[$(evt.srcElement).css("top").replace("px", "")].forEach(function(item) {
                            $.each(item.highlights, function(key, ann) {
                                $(ann).css("background-color", "rgba(255, 255, 10, 0.3)");
                            });
                        });
                        $(evt.srcElement).attr("data-selected", '1');
                    } else {
                        annotations.forEach(function(item) {
                            $(item).css("background-color", "inherit");
                        });
                        self.groupAndColor();
                        $(evt.srcElement).attr("data-selected", '0');
                    }
                });
            }
        });
        var self = this;
        var old = self.unfilteredAnnotations.length;
        setTimeout(function() {
            if (old !== self.unfilteredAnnotations.length) {
                self.reloadAnnotations();
            }
        }, 500);
        return;
    };
    
    /**
     * Function activated to turn grouping on or off
     */
    Grouping.prototype.groupingButtonPressed = function() {
        if(this.useGrouping === 1) {
        
            // grouping is cleared
            this.useGrouping = 0;
            this.clearGrouping();
            
            // remove the grouping functions from being activated by events
            this.annotator.unsubscribe('annotationsLoaded', this.reloadAnnotations);
            this.annotator.unsubscribe('annotationUploaded', this.reloadAnnotations);
            this.annotator.unsubscribe('annotationDeleted', this.reloadAnnotations);
            this.annotator.unsubscribe('annotationCreated', this.reloadAnnotations);
            
            // redraw button to turn grouping on/off
            $(".onOffGroupButton").html("Annotation Grouping: OFF");
            $(".onOffGroupButton").addClass("buttonOff");
            this.annotator.plugins.Store.annotations.forEach(function(annot) {
                $.each(annot.highlights, function(key, ann) {
                $(ann).css("background-color", "");
                });
            });
            
            // deals with the HighlightTags Plug-In
            this.annotator.publish('externalCallToHighlightTags');
            this.annotator.unsubscribe('colorizeCompleted', this.reloadAnnotations);
        } else {
        
            // runs reload/regroup annotations
            this.useGrouping = 1;
            this.reloadAnnotations();
            
            // subscribe again to the events triggered by annotations
            this.annotator.subscribe('annotationsLoaded', this.reloadAnnotations);
            this.annotator.subscribe('annotationUploaded', this.reloadAnnotations);
            this.annotator.subscribe('annotationDeleted', this.reloadAnnotations);
            this.annotator.subscribe('annotationCreated', this.reloadAnnotations);

            // redraw button to turn grouping on/off
            $(".onOffGroupButton").html("Annotation Grouping: ON");
            $(".onOffGroupButton").removeClass("buttonOff");
            this.annotator.subscribe('colorizeCompleted', this.reloadAnnotations);
        }
    }
    
    return Grouping;

})(Annotator.Plugin);