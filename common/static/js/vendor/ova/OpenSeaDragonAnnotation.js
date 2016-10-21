/* 
OpenSeaDragonAnnotation v1.0 (http://)
Copyright (C) 2014 CHS (Harvard University), Daniel Cebrián Robles and Phil Desenne
License: https://github.com/CtrHellenicStudies/OpenSeaDragonAnnotation/blob/master/License.rst

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
*/
(function($) {
    $.Viewer.prototype.annotation = function(options) {
        //-- wait for plugins --//
        var wrapper = jQuery('.annotator-wrapper').parent()[0],
            annotator = jQuery.data(wrapper, 'annotator'),
            self = this,
            isOpenViewer = false;
        
        /**
         * Sets up a call so that every time the OpenSeaDragon instance is opened
         * it triggers the annotations to be redrawn.
         */
        this.addHandler("open", function() {
            isOpenViewer = true;
            if (typeof self.annotationInstance!='undefined')
                self.annotationInstance.refreshDisplay();
        });
        annotator
            /**
             * This function is called once annotator has loaded the annotations.
             * It will then wait until the OSD instance has loaded to start drawing
             * the annotations.
             * @param Array annotations list of annotations from annotator instance
             */
            .subscribe("annotationsLoaded", function (annotations){
                if (!self.annotationInstance) {
                
                    // annotation instance should include the OSD item and annotator
                    self.annotationInstance = new $._annotation({
                        viewer: self,
                        annotator: annotator,
                    });
                    
                    // this collection of items is included as an item of annotator so
                    // that there is a method to communicate back and forth. 
                    annotator.osda = self.annotationInstance;
                    
                    // Because it takes a while for both OSD to open and for annotator
                    // to get items from the backend, we wait until we get the "open" call
                    function refreshDisplay(){
                        if(!isOpenViewer){
                            setTimeout(refreshDisplay,200);
                        }else{
                            self.annotationInstance.refreshDisplay();
                        }
                    }
                    refreshDisplay();
                } else {
                    self.annotationInstance.refreshDisplay();
                }
            });
    };
    
    /**
     * Instance of the annotation package including OSD and Annotator
     * @constructor
     */
    $._annotation = function(options) {
        // options
        options = options || {};
        if (!options.viewer) {
            throw new Error("A viewer must be specified.");
        }

        // variables
        this.viewer = options.viewer;
        this.annotator = options.annotator;
        this.options = options;
        this.isAnnotating = false; // If the user is annotating
        this.isDrawing = false; // if the user is drawing something
        this.rectPosition = undefined;
        
        // Init
        this.init();
    };
    
    //-- Methods
    $._annotation.prototype = {
        /**
         * This function makes sure that the OSD buttons are created, that the
         * panning and zooming functionality is created and the annotation events.
         */
        init: function(){
            var viewer = this.viewer;
            
            // create Buttons
            this._createNewButton();
            
            /* canvas Events */
            // Bind canvas functions
            var onCanvasMouseDown = this.__bind(this._onCanvasMouseDown,this);
            var onCanvasMouseMove = this.__bind(this._onCanvasMouseMove,this);
            var onDocumentMouseUp = this.__bind(this._onDocumentMouseUp,this);
                
            // Add canvas events
            $.addEvent(viewer.canvas, "mousedown", onCanvasMouseDown, true);
            $.addEvent(viewer.canvas, "mousemove", onCanvasMouseMove, true);
            $.addEvent(document, "mouseup", onDocumentMouseUp, true);
            
            // Viewer events
            var self = this;
        },
        
        /**
         * This function is called when the user changed from panning/zooming mode to
         * annotation creation mode. It allows the annotator to accept the creation of
         * a new annotation. 
         */
        newAnnotation:function(){
            var annotator = this.annotator;
            
            // This variable tells editor that we want create an image annotation
            annotator.editor.OpenSeaDragon = this.viewer.id;
            
            // allows the adder to actually show up
            annotator.adder.show();
            
            // takes into account the various wrappers and instances to put the shape
            // over the correct place. 
            this._setOverShape(annotator.adder);
            
            // Open a new annotator dialog
            annotator.onAdderClick();
        },
        
        /**
         * This function simply allows the editor to pop up with the given annotation.
         * @param {Object} annotation The annotation item from the backend server.
         * @param {TinyMCEEditor} editor The item that pops up when you edit an annotation.
         */
        editAnnotation: function(annotation,editor){
            // Stupid check: is the annotation you're trying to edit an image?
            if (this._isOpenSeaDragon(annotation)){
                
                var editor = editor || this.annotator.editor;
            
                // set the editor over the highlighted element
                this._setOverShape(editor.element);
                editor.checkOrientation();
            
                // makes sure that we are making an image annotation
                editor.OpenSeaDragon = this.viewer.id;
            }
        },
        
        /**
         * This function gets the annotations from the last annotator query and sorts
         * them and draws them onto the OpenSeaDragon instance. It also publishes
         * a notification in case the colorize the annotations. 
         */
        refreshDisplay: function(){
            var allannotations = this.annotator.plugins['Store'].annotations;
            var annotator = this.annotator;
        
            // Sort the annotations by date
            this._sortByDate(allannotations);
        
            // remove all of the overlays
            this.viewer.drawer.clearOverlays();
        
            for (var item in allannotations) {
                var an = allannotations[item];
            
                // check if the annotation is an OpenSeaDragon annotation
                if (this._isOpenSeaDragon(an)){
                    this.drawRect(an);    
                }
            }
            
            // if the colored highlights by tags plugin it is notified to colorize
            annotator.publish('externalCallToHighlightTags', [an]);
        },
        
        /**
         * This function get notified every time we switch from panning/zooming mode onto
         * annotation creation mode. 
         * @param {Event} e This is the event passed in from the OSD buttons.
         */
        modeAnnotation:function(e){
            this._reset();
            var viewer = this.viewer;
            if (!this.isAnnotating){
                // When annotating, the cursor turns into a crosshair and there is a
                // green border around the OSD instance.
                jQuery('.openseadragon1').css('cursor', 'crosshair');
                jQuery('.openseadragon1').css('border', '2px solid rgb(51,204,102)');
                e.eventSource.imgGroup.src =  this.resolveUrl( viewer.prefixUrl,"newan_hover.png");
                e.eventSource.imgRest.src =  this.resolveUrl( viewer.prefixUrl,"newan_hover.png");
                e.eventSource.imgHover.src = this.resolveUrl( viewer.prefixUrl,"newan_grouphover.png");
            }else{
                // Otherwise, the cursor is a cross with four arrows to indicate movement
                jQuery('.openseadragon1').css('cursor', 'all-scroll');
                jQuery('.openseadragon1').css('border', 'inherit');
                e.eventSource.imgGroup.src =  this.resolveUrl( viewer.prefixUrl,"newan_grouphover.png");
                e.eventSource.imgRest.src =  this.resolveUrl( viewer.prefixUrl,"newan_rest.png");
                e.eventSource.imgHover.src =  this.resolveUrl( viewer.prefixUrl,"newan_hover.png");
            }
            
            // toggles the annotating flag
            this.isAnnotating = !this.isAnnotating?true:false;
        },
        
        /**
         * This function takes in an annotation and draws the box indicating the area
         * that has been annotated. 
         * @param {Object} an Annotation item from the list in the Annotator instance.
         */
        drawRect:function(an){
            // Stupid check: Does this annotation actually have an area of annotation
            if (typeof an.rangePosition!='undefined'){
                // Sets up the visual aspects of the area for the user
                var span = document.createElement('span');
                var rectPosition = an.rangePosition;
                span.className = "annotator-hl";
                
                // outline and border below create a double line one black and one white
                // so to be able to differentiate when selecting dark or light images
                span.style.border = '2px solid rgb(255, 255, 255)';
                span.style.outline = '2px solid rgb(0, 0, 0)';
                span.style.background = 'rgba(0,0,0,0)';
                
                // Adds listening items for the viewer and editor
                var onAnnotationMouseMove = this.__bind(this._onAnnotationMouseMove,this);
                var onAnnotationClick = this.__bind(this._onAnnotationClick,this);
                $.addEvent(span, "mousemove", onAnnotationMouseMove, true);
                $.addEvent(span, "click", onAnnotationClick, true);
                
                // Set the object in the div
                jQuery.data(span, 'annotation', an);
                
                // Add the highlights to the annotation
                an.highlights = jQuery(span);
                
                // Sends the element created to the proper location within the OSD instance
                var olRect = new OpenSeadragon.Rect(rectPosition.left, rectPosition.top, rectPosition.width, rectPosition.height);
                return this.viewer.drawer.addOverlay({
                    element: span,
                    location: olRect,
                    placement: OpenSeadragon.OverlayPlacement.TOP_LEFT
                });
            }
            return false;
        },
        
        /**
         * This changes the variable rectPosition to the proper location based on
         * screen coordinates and OSD image coordinates. 
         */
        setRectPosition:function(){
            // Get the actual locations of the rectangle
            var left = parseInt(this.rect.style.left);
            var top = parseInt(this.rect.style.top);
            var width = parseInt(this.rect.style.left) + parseInt(this.rect.style.width);
            var height = parseInt(this.rect.style.top) + parseInt(this.rect.style.height);
            var startPoint = new $.Point(left,top);
            var endPoint = new $.Point(width,height);
            
            // return the proper value of the rectangle
            this.rectPosition = {left:this._physicalToLogicalXY(startPoint).x,
                top:this._physicalToLogicalXY(startPoint).y,
                width:this._physicalToLogicalXY(endPoint).x - this._physicalToLogicalXY(startPoint).x,
                height:this._physicalToLogicalXY(endPoint).y - this._physicalToLogicalXY(startPoint).y
            };
        },
        
        /* Handlers */
        
        /**
         * When the user starts clicking this will create a rectangle that will be a
         * temporary position that is to be later scaled via dragging
         * @param {Event} event The actual action of clicking down.
         */
        _onCanvasMouseDown: function(event) {
            
            // action is ONLY performed if we are in annotation creation mode
            if (this.isAnnotating){
                var viewer = this.viewer;
                event.preventDefault();
                
                // reset the display
                this._reset();
                
                // set mode drawing
                this.isDrawing = true;
                
                // Create rect element
                var mouse  = $.getMousePosition( event );
                var elementPosition = $.getElementPosition(viewer.canvas);
                var position = mouse.minus( elementPosition );
                viewer.innerTracker.setTracking(false);
                this.rect = document.createElement('div');
                this.rect.style.background = 'rgba(0,0,0,0)';
                
                // outline and border below create a double line one black and one white
                // so to be able to differentiate when selecting dark or light images
                this.rect.style.border = '2px solid rgb(255, 255, 255)';
                this.rect.style.outline = '2px solid rgb(0, 0, 0)';
                
                this.rect.style.position = 'absolute';
                this.rect.className = 'DrawingRect';
                // set the initial position
                this.rect.style.top = position.y + "px";
                this.rect.style.left = position.x + "px";
                this.rect.style.width = "1px";
                this.rect.style.height = "1px";
                
                // save the start Position
                this.startPosition = position;
                // save rectPosition as initial rectangle parameter to Draw in the canvas
                this.setRectPosition();
                
                // append Child to the canvas
                viewer.canvas.appendChild(this.rect);
            }
        },
        /**
         * When the user has clicked and is now dragging to create an annotation area,
         * the following function resizes the area selected. 
         * @param {Event} event The actual action of dragging every time it is dragged.
         */
        _onCanvasMouseMove: function(event) {
        
            // of course, this only runs when we are in annotation creation mode and
            // when the user has clicked down (and is therefore drawing the rectangle)
            if (this.isAnnotating && this.isDrawing){ 
                var viewer = this.viewer;
                
                // Calculate the new end position
                var mouse  = $.getMousePosition( event );
                var elementPosition = $.getElementPosition(viewer.canvas);
                var endPosition = mouse.minus( elementPosition );
                // retrieve start position    
                var startPosition = this.startPosition;
                
                var newWidth= endPosition.x-startPosition.x;
                var newHeight =endPosition.y-startPosition.y;
                
                // Set new position
                this.rect.style.width = (newWidth < 0) ? (-1*newWidth) + 'px' : newWidth + 'px';
                this.rect.style.left = (newWidth < 0) ? (startPosition.x + newWidth) + 'px' : startPosition.x + 'px';
                this.rect.style.height = (newHeight < 0) ? (-1*newHeight) + 'px' : newHeight + 'px';
                this.rect.style.top = (newHeight < 0) ? (startPosition.y + newHeight) + 'px' : startPosition.y + 'px';
                
                // Modify the rectPosition with the new this.rect values
                this.setRectPosition();
                
                // Show adder and hide editor
                this.annotator.editor.element[0].style.display = 'none';
                this._setOverShape(this.annotator.adder);
            }
        },
        
        /**
         * This function will finish drawing the rectangle, get its current position
         * and then open up the editor to make the annotation.
         */
        _onDocumentMouseUp: function() {
        
            // Stupid check: only do it when in annotation creation mode and
            // when the user has begun making a rectangle over the annotation area
            if (this.isAnnotating && this.isDrawing){
                var viewer = this.viewer;
                
                viewer.innerTracker.setTracking(true);
                this.isDrawing = false;
                
                // Set the new position for the rectangle
                this.setRectPosition();
                
                // Open Annotator editor
                this.newAnnotation();
                
                // Hide adder and show editor
                this.annotator.editor.element[0].style.display = 'block';
                this._setOverShape(this.annotator.editor.element);
                this.annotator.editor.checkOrientation();
            }
        },
        
        /**
         * This function will trigger the viewer to show up whenever an item is hovered
         * over and will cause the background color of the area to change a bit.
         * @param {Event} event The actual action of moving the mouse over an element.
         */
        _onAnnotationMouseMove: function(event){
            var annotator = this.annotator;
            var elem = jQuery(event.target).parents('.annotator-hl').andSelf();
            
            // if there is a opened annotation then show the new annotation mouse over
            if (typeof annotator!='undefined' && elem.hasClass("annotator-hl") && !this.isDrawing){
                // hide the last open viewer
                annotator.viewer.hide();
                // get the annotation over the mouse
                var annotations = jQuery(event.target.parentNode).find('.annotator-hl').map(function() {
                    var self = jQuery(this);
                    var offset = self.offset();
                    var l = offset.left;
                    var t = offset.top;
                    var h = self.height();
                    var w = self.width();
                    var x = $.getMousePosition(event).x;
                    var y = $.getMousePosition(event).y;

                    var maxx = l + w;
                    var maxy = t + h;
                    
                    // if the current position of the mouse is within the bounds of an area
                    // change the background of that area to a light yellow to simulate
                    // a hover. Otherwise, keep it translucent.
                    this.style.background = (y <= maxy && y >= t) && (x <= maxx && x >= l)?
                        'rgba(255, 255, 10, 0.05)':'rgba(0, 0, 0, 0)';
                    
                    return (y <= maxy && y >= t) && (x <= maxx && x >= l)? jQuery(this).data("annotation") : null;
                });
                // show the annotation in the viewer
                var mousePosition = {
                    top:$.getMousePosition(event).y,
                    left:$.getMousePosition(event).x,
                };
                // if the user is hovering over multiple annotation areas, 
                // they will be stacked as usual
                if (annotations.length>0) annotator.showViewer(jQuery.makeArray(annotations), mousePosition);
            }
        },
        
        /**
         * This function will zoom/pan the user into the bounding area of the annotation.
         * @param {Event} event The actual action of clicking down within an annotation area.
         */
        _onAnnotationClick: function(event){
            // gets the annotation from the data stored in the element
            var an = jQuery.data(event.target, 'annotation');
            // gets the bound within the annotation data
            var bounds = typeof an.bounds!='undefined'?an.bounds:{};
            var currentBounds = this.viewer.drawer.viewport.getBounds();
            // if the area is not already panned and zoomed in to the correct area
            if (typeof bounds.x!='undefined') currentBounds.x = bounds.x;
            if (typeof bounds.y!='undefined') currentBounds.y = bounds.y;
            if (typeof bounds.width!='undefined') currentBounds.width = bounds.width;
            if (typeof bounds.height!='undefined') currentBounds.height = bounds.height;
            // change the zoom to the saved parameter
            this.viewer.drawer.viewport.fitBounds(currentBounds);
        },
        
        /* Utilities */
        /**
         * This function will return an array of sorted items
         * @param {Array} annotations List of annotations from annotator instance.
         * @param {String} type Either 'asc' for ascending or 'desc' for descending
         */
        _sortByDate: function (annotations,type){
            var type = type || 'asc'; // asc => The value [0] will be the most recent date
            annotations.sort(function(a,b){
                // gets the date from when they were last updated
                a = new Date(typeof a.updated!='undefined'?createDateFromISO8601(a.updated):'');
                b = new Date(typeof b.updated!='undefined'?createDateFromISO8601(b.updated):'');
                
                // orders them based on type passed in
                if (type == 'asc')
                    return b<a?-1:b>a?1:0;
                else
                    return a<b?-1:a>b?1:0;
            });
        },
        /**
         * This function creates the button that will switch back and forth between
         * annotation creation mode and panning/zooming mode.
         */
        _createNewButton:function(){
            var viewer = this.viewer;
            var onFocusHandler          = $.delegate( this, onFocus );
            var onBlurHandler           = $.delegate( this, onBlur );
            var onModeAnnotationHandler  = $.delegate( this, this.modeAnnotation );
            /* Buttons */
            var viewer = this.viewer;
            var self = this;
            viewer.modeAnnotation = new $.Button({
                element:    viewer.modeAnnotation ? $.getElement( viewer.modeAnnotation ) : null,
                clickTimeThreshold: viewer.clickTimeThreshold,
                clickDistThreshold: viewer.clickDistThreshold,
                tooltip:    "New Annotation",
                srcRest:    self.resolveUrl( viewer.prefixUrl,"newan_rest.png"),
                srcGroup:      self.resolveUrl( viewer.prefixUrl,"newan_grouphover.png"),
                srcHover:   self.resolveUrl( viewer.prefixUrl,"newan_hover.png"),
                srcDown:    self.resolveUrl( viewer.prefixUrl,"newan_pressed.png"),
                onRelease:  onModeAnnotationHandler,
                onFocus:    onFocusHandler,
                onBlur:     onBlurHandler
            });
            
            //- Wrapper Annotation Menu
            viewer.wrapperAnnotation = new $.ButtonGroup({
                buttons: [
                    viewer.modeAnnotation,
                ],
                clickTimeThreshold: viewer.clickTimeThreshold,
                clickDistThreshold: viewer.clickDistThreshold
            });
            
            // area makes sure that the annotation button only appears when everyone is
            // allowed to annotate or if you are an instructor
            if(this.options.viewer.annotation_mode == "everyone" || this.options.viewer.flags){
                /* Set elements to the control menu */
                viewer.annotatorControl  = viewer.wrapperAnnotation.element;
                if( viewer.toolbar ){
                    viewer.toolbar.addControl(
                        viewer.annotatorControl,
                        {anchor: $.ControlAnchor.BOTTOM_RIGHT}
                    );
                }else{
                    viewer.addControl(
                        viewer.annotatorControl,
                        {anchor: $.ControlAnchor.TOP_LEFT}
                    );
                }
            }
        },
        
        /**
         * This function makes sure that if you're switching to panning/zooming mode,
         * the last rectangle you drew (but didn't save) gets destroyed.
         */
        _reset: function(){
            // Find and remove DrawingRect. This is the previous rectangle
            this._removeElemsByClass('DrawingRect',this.viewer.canvas);
            
            // Show adder and hide editor
            this.annotator.editor.element[0].style.display = 'none';
        },
        
        /**
         * This function binds the function to the object it was created from
         * @param {function} fn This is the function you want to apply
         * @param {Object} me This is the object you should pass it to (usually itself)
         */
        __bind: function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
        
        /**
         * Remove all the elements with a given name inside "inElement" to maintain
         * a limited scope.
         * @param {String} className Class that should be removed
         * @param {HTMLElement} inElement Element in which classes should be removed
         */
        _removeElemsByClass: function(className,inElement){
            var className = className || '';
            var inElement = inElement || {};
            divs = inElement.getElementsByClassName(className);
            for(var i = 0; i < divs.length; i++) {
                divs[i].remove();
            }
        },
        
        /** 
         * Detect if the annotation is an image annotation and there's a target, open
         * OSD instance.
         * @param {Object} an Annotation from the Annotator instance
         */
        _isOpenSeaDragon: function (an){
            var annotator = this.annotator;
            var rp = an.rangePosition;
            
            // Makes sure OSD exists and that annotation is an image annotation
            // with a position in the OSD instance
            var isOpenSeaDragon = (typeof annotator.osda != 'undefined');
            var isContainer = (typeof an.target!='undefined' && an.target.container==this.viewer.id );
            var isImage = (typeof an.media!='undefined' && an.media=='image');
            var isRP = (typeof rp!='undefined');
            var isSource = false;
            
            // Though it would be better to store server ids of images in the annotation that
            // would require changing annotations that were already made, instead we check if
            // the id is a substring of the thumbnail, which according to OpenSeaDragon API should be the case.
            var sourceId = this.viewer.source['@id'];

            // code runs on annotation creation before thumbnail is created
            var targetThumb = an.target ? an.target.thumb : false;
            if (isContainer) {
                // reason why this is okay is that we are trying to ascertain that the annotation
                // is related to the image drawn. If thumbnail attribute is empty it means the annotation
                // was just created and should still be considered an annotation of this image.
                isSource = targetThumb ? (targetThumb.indexOf(sourceId) !== -1) : true;
            }            
            return (isOpenSeaDragon && isContainer && isImage && isRP && isSource);
        },
        
        /* Annotator Utilities */
        /**
         * Makes sure that absolute x and y values for overlayed section are
         * calculated to match area within OSD instance
         * @param {HTMLElement} elem Element where shape is overlayed
         */
        _setOverShape: function(elem){
            // Calculate Point absolute positions 
            var rectPosition = this.rectPosition || {};
            var startPoint = this._logicalToPhysicalXY(new $.Point(rectPosition.left,rectPosition.top));
            var endPoint = this._logicalToPhysicalXY(new $.Point(rectPosition.left + rectPosition.width,rectPosition.top + rectPosition.height));
            
            // Calculate Point absolute positions    
            var wrapper = jQuery('.annotator-wrapper')[0];
            var positionAnnotator = $.getElementPosition(wrapper);
            var positionCanvas = $.getElementPosition(this.viewer.canvas);
            var positionAdder = {};
            
            // Fix with positionCanvas based on annotator wrapper and OSD area
            startPoint = startPoint.plus(positionCanvas);
            endPoint = endPoint.plus(positionCanvas);
            
            elem[0].style.display = 'block'; // Show the adder
        
            positionAdder.left = (startPoint.x - positionAnnotator.x) + (endPoint.x - startPoint.x) / 2;
            positionAdder.top =  (startPoint.y - positionAnnotator.y) + (endPoint.y - startPoint.y) / 2; // It is not necessary fix with - positionAnnotator.y
            elem.css(positionAdder);
        },
        
        resolveUrl: function( prefix, url ) {
            return prefix ? prefix + url : url;
        },
        
        /* Canvas Utilities */
        /**
         * Given a point of x and y values in pixels it will return a point with
         * percentages in relation to the Image object
         * @param {$.Point} point Canvas relative coordinates in pixels
         * @return {$.Point} Returns Image relative percentages
         */
        _physicalToLogicalXY: function(point){
            var point = typeof point!='undefined'?point:{};
            var boundX = this.viewer.viewport.getBounds(true).x;
            var boundY = this.viewer.viewport.getBounds(true).y;
            var boundWidth = this.viewer.viewport.getBounds(true).width;
            var boundHeight = this.viewer.viewport.getBounds(true).height;
            var containerSizeX = this.viewer.viewport.getContainerSize().x;
            var containerSizeY = this.viewer.viewport.getContainerSize().y;
            var x = typeof point.x!='undefined'?point.x:0;
            var y = typeof point.y!='undefined'?point.y:0;
            x = boundX + ((x / containerSizeX) * boundWidth);
            y = boundY + ((y / containerSizeY) * boundHeight);
            return new $.Point(x,y);
        },
        
        /**
         * Given values in percentage relatives to the image it will return a point in
         * pixels related to the canvas element.
         * @param {$.Point} point Image relative percentages
         * @return {$.Point} Returns canvas relative coordinates in pixels
         */
        _logicalToPhysicalXY: function(point){
            var point = typeof point!='undefined'?point:{};
            var boundX = this.viewer.viewport.getBounds(true).x;
            var boundY = this.viewer.viewport.getBounds(true).y;
            var boundWidth = this.viewer.viewport.getBounds(true).width;
            var boundHeight = this.viewer.viewport.getBounds(true).height;
            var containerSizeX = this.viewer.viewport.getContainerSize().x;
            var containerSizeY = this.viewer.viewport.getContainerSize().y;
            var x = typeof point.x!='undefined'?point.x:0;
            var y = typeof point.y!='undefined'?point.y:0;
            x = (x - boundX) * containerSizeX / boundWidth;
            y = (y - boundY) * containerSizeY / boundHeight;
            return new $.Point(x,y);
        },
    }
    
    /* General functions */
    /**
     * initiates an animation to hide the controls
     */
    function beginControlsAutoHide( viewer ) {
        if ( !viewer.autoHideControls ) {
            return;
        }
        viewer.controlsShouldFade = true;
        viewer.controlsFadeBeginTime =
            $.now() +
            viewer.controlsFadeDelay;

        window.setTimeout( function(){
            scheduleControlsFade( viewer );
        }, viewer.controlsFadeDelay );
    }
    /**
     * stop the fade animation on the controls and show them
     */
    function abortControlsAutoHide( viewer ) {
        var i;
        viewer.controlsShouldFade = false;
        for ( i = viewer.controls.length - 1; i >= 0; i-- ) {
            viewer.controls[ i ].setOpacity( 1.0 );
        }
    }
    function onFocus(){
        abortControlsAutoHide( this.viewer );
    }

    function onBlur(){
        beginControlsAutoHide( this.viewer );
    }
    
    
})(OpenSeadragon);



//----------------Plugin for Annotator to setup OpenSeaDragon----------------//

Annotator.Plugin.OpenSeaDragon = (function(_super) {
    __extends(OpenSeaDragon, _super);

    /**
     * Creates an instance of the plugin that interacts with OpenSeaDragon.
     * @constructor
     */
    function OpenSeaDragon() {
        this.pluginSubmit = __bind(this.pluginSubmit, this);
        _ref = OpenSeaDragon.__super__.constructor.apply(this, arguments);
        
        // To facilitate calling items, we want to be able to get the index of a value 
        this.__indexOf = [].indexOf; 
        if(!this.__indexOf){
        
            // Basically you iterate through every item on the list, if it matches
            // the item you are looking for return the current index, otherwise return -1
            this.__indexOf = function(item) { 
                for (var i = 0, l = this.length; i < l; i++) { 
                    if (i in this && this[i] === item) 
                        return i; 
                } 
                return -1; 
            }

        }
        return _ref;
    }

    OpenSeaDragon.prototype.field = null;
    OpenSeaDragon.prototype.input = null;
    
    /**
     * This function initiates the editor that will apear when you edit/create an
     * annotation and the viewer that appears when you hover over an item.
     */
    OpenSeaDragon.prototype.pluginInit = function() {
        // Check that annotator is working
        if (!Annotator.supported()) {
            return;
        }
        
        //-- Editor
        this.field = this.annotator.editor.addField({
            id: 'osd-input-rangePosition-annotations',
            type: 'input', // options (textarea,input,select,checkbox)
            submit: this.pluginSubmit,
            EditOpenSeaDragonAn: this.EditOpenSeaDragonAn
        });
        
        // Modify the element created with annotator to be an invisible span
        var select = '<li><span id="osd-input-rangePosition-annotations"></span></li>';
        var newfield = Annotator.$(select);
        Annotator.$(this.field).replaceWith(newfield);
        this.field=newfield[0];

        //-- Listener for OpenSeaDragon Plugin
        this.initListeners();
        
        return this.input = $(this.field).find(':input');
    }
    
    /**
     * This function is called by annotator whenever user hits the "Save" Button. It will
     * first check to see if the user is editing or creating and then save the
     * metadata for the image in an object that will be passed to the backend. 
     */
    OpenSeaDragon.prototype.pluginSubmit = function(field, annotation) {
        // Select the new JSON for the Object to save
        if (this.EditOpenSeaDragonAn()){
            var annotator = this.annotator;
            var osda = annotator.osda;
            var position = osda.rectPosition || {};
            var isNew = typeof annotation.media=='undefined';
            if(isNew){
                // if it's undefined, we know it's an image because the editor within
                // the OSD instance was open
                if (typeof annotation.media == 'undefined') annotation.media = "image"; // - media
                annotation.target = annotation.target || {}; // - target
                annotation.target.container = osda.viewer.id || ""; // - target.container
                
                // Save source url
                var source = osda.viewer.source;
                var tilesUrl = typeof source.tilesUrl!='undefined'?source.tilesUrl:'';
                var functionUrl = typeof source.getTileUrl!='undefined'?source.getTileUrl():'';
                annotation.target.src = tilesUrl!=''?tilesUrl:('' + functionUrl).replace(/\s+/g, ' '); // - target.src (media source)
                annotation.target.ext = source.fileFormat || ""; // - target.ext (extension)
                
                // Gets the bounds in order to save them for zooming in and highlight properties
                annotation.bounds = osda.viewer.drawer.viewport.getBounds() || {}; // - bounds
                var finalimagelink = source["@id"].replace("/info.json", "");
                var highlightX = Math.round(position.left * source["width"]);
                var highlightY = Math.round(position.top * source["width"]);
                var highlightWidth = Math.round(position.width * source["width"]);
                var highlightHeight = Math.round(position.height * source["width"]);
                
                // creates a link to the OSD server that contains the image to get
                // the thumbnail of the selected portion of the image
                annotation.target.thumb = finalimagelink + "/" + highlightX + "," + highlightY + "," + highlightWidth + "," + highlightHeight + "/full/0/native." + source["formats"][0];
                if(isNew) annotation.rangePosition =     position || {};    // - rangePosition
                
                // updates the dates associated with creation and update
                annotation.updated = new Date().toISOString(); // - updated
                if (typeof annotation.created == 'undefined')
                    annotation.created = annotation.updated; // - created
            }
        }
        return annotation.media;
    };
    
    
    //------ Methods    ------//
    /**
     * Detect if we are creating or editing an OpenSeaDragon annotation
     */
    OpenSeaDragon.prototype.EditOpenSeaDragonAn =  function (){
        var wrapper = $('.annotator-wrapper').parent()[0],
            annotator = window.annotator = $.data(wrapper, 'annotator'),
            isOpenSeaDragon = (typeof annotator.osda != 'undefined'),
            OpenSeaDragon = annotator.editor.OpenSeaDragon;
        return (isOpenSeaDragon && typeof OpenSeaDragon!='undefined' && OpenSeaDragon!==-1);
    };
    
    /** 
     * Detect if the annotation is an image annotation and there's a target, open
     * OSD instance.
     * @param {Object} an Annotation from the Annotator instance
     */
    OpenSeaDragon.prototype.isOpenSeaDragon = function (an){
        var annotator = this.annotator;
        var rp = an.rangePosition;
        
        // Makes sure OSD exists and that annotation is an image annotation
        // with a position in the OSD instance
        var isOpenSeaDragon = (typeof annotator.osda != 'undefined');
        var isContainer = (typeof an.target!='undefined' && an.target.container==osda.viewer.id );
        var isImage = (typeof an.media!='undefined' && an.media=='image');
        var isRP = (typeof rp!='undefined');
        var isSource = false;
        
        // Double checks that the image being displayed matches the annotations 
        var source = osda.viewer.source;
        var tilesUrl = typeof source.tilesUrl!='undefined'?source.tilesUrl:'';
        var functionUrl = typeof source.getTileUrl!='undefined'?source.getTileUrl:'';
        var compareUrl = tilesUrl!=''?tilesUrl:('' + functionUrl).replace(/\s+/g, ' ');
        if(isContainer) isSource = (an.target.src == compareUrl);
        
        return (isOpenSeaDragon && isContainer && isImage && isRP && isSource);
    };
    
    /**
     * Deletes the OSD annotation from Annotator and refreshes display to remove element
     * @param {Object} an Annotation object from the Annotator instance
     */
    OpenSeaDragon.prototype._deleteAnnotation = function(an){
        // Remove the annotation of the plugin Store
        var annotations = this.annotator.plugins['Store'].annotations;
        
        // Failsafe in case annotation is not immediately removed from annotations list
        if (annotations.indexOf(an)>-1)
            annotations.splice(annotations.indexOf(an), 1);
        
        // Refresh the annotations in the display
        this.annotator.osda.refreshDisplay();
    };
    
    
    //--Listeners
    OpenSeaDragon.prototype.initListeners = function (){
        var wrapper = $('.annotator-wrapper').parent()[0];
        var annotator = $.data(wrapper, 'annotator');
        var EditOpenSeaDragonAn = this.EditOpenSeaDragonAn;
        var isOpenSeaDragon = this.isOpenSeaDragon;
        var self = this;
            
        // local functions
        //-- Editor
        function annotationEditorHidden(editor) {
            if (EditOpenSeaDragonAn()){
                annotator.osda._reset();
                annotator.osda.refreshDisplay(); // Reload the display of annotations
            }
            annotator.editor.OpenSeaDragon=-1;
            annotator.unsubscribe("annotationEditorHidden", annotationEditorHidden);
        };
        function annotationEditorShown(editor,annotation) {
            annotator.osda.editAnnotation(annotation,editor);
            annotator.subscribe("annotationEditorHidden", annotationEditorHidden);
        };
        //-- Annotations
        function annotationDeleted(annotation) {
            if (isOpenSeaDragon(annotation))
                self._deleteAnnotation(annotation);
        };
        //-- Viewer
        function hideViewer(){
            jQuery(annotator.osda.viewer.canvas.parentNode).find('.annotator-hl').map(function() {
                return this.style.background = 'rgba(0, 0, 0, 0)';
            });
            annotator.viewer.unsubscribe("hide", hideViewer);
        };
        function annotationViewerShown(viewer,annotations) {
            var wrapper = jQuery('.annotator-wrapper').offset();

            // Fix with positionCanvas
            var startPoint = {x: parseFloat(viewer.element[0].style.left),
                y: parseFloat(viewer.element[0].style.top)};
        
            var separation = viewer.element.hasClass(viewer.classes.invert.y)?5:-5,
                newpos = {
                    top: (startPoint.y - wrapper.top)+separation,
                    left: (startPoint.x - wrapper.left)
                };
            viewer.element.css(newpos);
            
            // Remove the time to wait until disapear, to be more faster that annotator by default
            viewer.element.find('.annotator-controls').removeClass(viewer.classes.showControls);
            
            annotator.viewer.subscribe("hide", hideViewer);
        };    
        // subscribe to Annotator
        annotator.subscribe("annotationEditorShown", annotationEditorShown)
            .subscribe("annotationDeleted", annotationDeleted)
            .subscribe("annotationViewerShown", annotationViewerShown);
    }

    return OpenSeaDragon;

})(Annotator.Plugin);



//----------------PUBLIC OBJECT TO CONTROL THE ANNOTATIONS----------------//

// The name of the plugin that the user will write in the html
OpenSeadragonAnnotation = ("OpenSeadragonAnnotation" in window) ? OpenSeadragonAnnotation : {};

OpenSeadragonAnnotation = function (element, options) {
    // local variables
    var $ = jQuery;
    var options = options || {};
    options.optionsOpenSeadragon = options.optionsOpenSeadragon || {};
    options.optionsOSDA = options.optionsOSDA || {};
    options.optionsAnnotator = options.optionsAnnotator || {};
    
    // if there isn't store optinos it will create a uri and limit variables for the Back-end of Annotations 
    if (typeof options.optionsAnnotator.store=='undefined')
        options.optionsAnnotator.store = {};
    var store = options.optionsAnnotator.store;
    if (typeof store.annotationData=='undefined')
        store.annotationData = {};
    if (typeof store.annotationData.uri=='undefined'){
        var uri = location.protocol + '//' + location.host + location.pathname;
        store.annotationData.store = {uri:uri};
    }
    if (typeof store.loadFromSearch=='undefined')
        store.loadFromSearch={};
    if (typeof store.loadFromSearch.uri=='undefined')
        store.loadFromSearch.uri = uri;
    if (typeof store.loadFromSearch.limit=='undefined')
        store.loadFromSearch.limit = 10000;
        
    // global variables
    this.currentUser = null;

    //-- Init all the classes --/
    // Annotator
    this.annotator = $(element).annotator(options.optionsAnnotator.annotator).data('annotator');
    
    //-- Activate all the Annotator plugins --//
    if (typeof options.optionsAnnotator.auth!='undefined')
        this.annotator.addPlugin('Auth', options.optionsAnnotator.auth);
        
    if (typeof options.optionsAnnotator.permissions!='undefined')
        this.annotator.addPlugin("Permissions", options.optionsAnnotator.permissions);
    
    if (typeof options.optionsAnnotator.store!='undefined')
        this.annotator.addPlugin("Store", options.optionsAnnotator.store);
            
    if (typeof Annotator.Plugin["Geolocation"] === 'function') 
        this.annotator.addPlugin("Geolocation",options.optionsAnnotator.geolocation);
        
    if (typeof Annotator.Plugin["Share"] === 'function') 
        this.annotator.addPlugin("Share",options.optionsAnnotator.share);
        
    if (typeof Annotator.Plugin["RichText"] === 'function') 
        this.annotator.addPlugin("RichText",options.optionsAnnotator.richText);
        
    if (typeof Annotator.Plugin["Reply"] === 'function') 
        this.annotator.addPlugin("Reply");
        
    if (typeof Annotator.Plugin["OpenSeaDragon"] === 'function') 
        this.annotator.addPlugin("OpenSeaDragon");
            
    if (typeof Annotator.Plugin["Flagging"] === 'function') 
        this.annotator.addPlugin("Flagging");

    if (typeof Annotator.Plugin["HighlightTags"] === 'function')
        this.annotator.addPlugin("HighlightTags", options.optionsAnnotator.highlightTags);

    //- OpenSeaDragon
    this.viewer =  OpenSeadragon(options.optionsOpenSeadragon);
    //- OpenSeaDragon Plugins
    this.viewer.annotation(options.optionsOSDA);
    
    // Set annotator.editor.OpenSeaDragon by default
    this.annotator.editor.OpenSeaDragon=-1;
    
    // We need to make sure that osda is accessible via annotator
    this.annotator.osda = this;

    function reloadEditor(){
        tinymce.EditorManager.execCommand('mceRemoveEditor',true, "annotator-field-0");
        tinymce.EditorManager.execCommand('mceAddEditor',true, "annotator-field-0");
        
        // if person hits into/out of fullscreen before closing the editor should close itself
        // ideally we would want to keep it open and reposition, this would make a great TODO in the future
        annotator.editor.hide();
    }

    var self = this;
    document.addEventListener("fullscreenchange", function () {
        reloadEditor();
    }, false);
 
    document.addEventListener("mozfullscreenchange", function () {
        reloadEditor();
    }, false);
 
    document.addEventListener("webkitfullscreenchange", function () {
        reloadEditor();
    }, false);
 
    document.addEventListener("msfullscreenchange", function () {
        reloadEditor();
    }, false);

    // for some reason the above doesn't work when person hits ESC to exit full screen...
    $(document).keyup(function(e) {
        // esc key reloads editor as well
        if (e.keyCode == 27) { 
            reloadEditor();
        }   
    });
    
    this.options = options;

    return this;
}


        