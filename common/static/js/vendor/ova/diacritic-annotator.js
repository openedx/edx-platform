/* 
 Diacritic Annotator Plugin v1.0 (https://github.com/lduarte1991/diacritic-annotator)
 Copyright (C) 2014 Luis F Duarte
 License: https://github.com/lduarte1991/diacritic-annotator/blob/master/LICENSE.rst
 
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
 
var _ref;
var __bind = function(fn, me){ 
    return function(){ 
        return fn.apply(me, arguments); 
    }; 
};
var __hasProp = {}.hasOwnProperty;
var __extends = function(child, parent) { 
    for (var key in parent) { 
        if (__hasProp.call(parent, key)) 
            child[key] = parent[key]; 
    } 
    function ctor() { this.constructor = child; } 
    ctor.prototype = parent.prototype; 
    child.prototype = new ctor(); 
    child.__super__ = parent.prototype; 
    return child; 
};

Annotator.Plugin.Diacritics = (function(_super) {
    __extends(Diacritics, _super);
    
    //Options will include diacritic name, picture used, baseline
    Diacritics.prototype.options = null;
    Diacritics.prototype.diacriticmarks = null;
    
    /**
     * Declares all the functions and variables that the plugin will need.
     * @constructor
     */
    function Diacritics(element,options) {
        this.pluginSubmit = __bind(this.pluginSubmit, this);
        this.updateDiacritics = __bind(this.updateDiacritics, this);
        this.updateViewer = __bind(this.updateViewer, this);
        this.getDiacritics = __bind(this.getDiacritics, this);
        this.getPos = __bind(this.getPos, this);
        this.putMarkAtLocation = __bind(this.putMarkAtLocation, this);
        this.updateEditorForDiacritics = 
            __bind(this.updateEditorForDiacritics, this);
        
        this.options = options;
        this.diacriticmarks = this.getDiacritics();
        _ref = Diacritics.__super__.constructor.apply(this, arguments);
        return _ref;
    }
    
    //example variables to be used to receive input in the annotator view
    Diacritics.prototype.field = null;
    Diacritics.prototype.input = null;
    
    /**
     * Initalizes the Plug-in for diacritic marks. It adds in the field for the mark
     * and sets up listeners from the Annotator.js file to make changes as needed
     */
    Diacritics.prototype.pluginInit = function() {        
        //Check that annotator is working
        if (!Annotator.supported()) {
            return;
        }
        var di = this.diacriticmarks;
        
        //-- Editor
        var self = this;
        if(di != 'undefined'){
            $.each(di,function(item){
                self.field = self.annotator.editor.addField({
                    //options (textarea,input,select,checkbox)
                    type: 'checkbox', 
                    label: Annotator._t(item),
                    submit: self.pluginSubmit,
                });
            });
        
            //-- Viewer
            this.annotator.viewer.addField({
                load: this.updateViewer,
            });

            this.annotator.subscribe('annotationsLoaded', this.updateDiacritics);
            this.annotator.subscribe('annotationUploaded', this.updateDiacritics);
            this.annotator.subscribe('annotationDeleted', this.updateDiacritics);
            this.annotator.subscribe('annotationUpdated', this.updateDiacritics);
            this.annotator.subscribe('annotationEditorShown', this.updateEditorForDiacritics, this.field);
            
            $(window).resize(this.updateDiacritics.bind(this));
        }
        
        return this.input = $(this.field).find(':input');
    };
    
    /**
     * Adds or removes tag from checked/unchecked boxes of diacritics available
     * @param field {Object} - element which holds editor
     * @param annotation {Object} - object that contains annotation information from database
     */
    Diacritics.prototype.pluginSubmit = function(field, annotation) {
        var checkedItems = $(this.field).find(':input');
        var self = this;
        $.each(checkedItems, function(item){
            if(typeof annotation.tags != 'undefined'){
                var index = $.inArray(checkedItems[item].placeholder, annotation.tags);
                if(index != -1){
                    annotation.tags.splice(index, 1);  
                    var annotatorWrapper = $('.annotator-wrapper').first();
                    var element = annotatorWrapper.find('div.' + annotation.id);
                    
                    if(!element.length){
                        element = annotatorWrapper.find('div.undefined');
                    }
                    
                    element.remove();
                }
               
                if(checkedItems[item].checked === true){
                    annotation.tags.unshift(checkedItems[item].placeholder);
                    self.putMarkAtLocation(annotation,  checkedItems[item].placeholder);
                }
            } else {
                if(checkedItems[item].checked === true){
                    annotation.tags = [checkedItems[item].placeholder];
                    self.putMarkAtLocation(annotation, checkedItems[item].placeholder);
                }
            }
        });
        
    };

    /**
     * Draws the mark above a specific annotation
     * @param annotation {Object} - location where mark should go
     * @param mark {string}- type of mark that should go above annotation
     */
    Diacritics.prototype.putMarkAtLocation = function (annotation, mark){
        var loc = this.getPos(annotation.highlights[0]);
        var alignment = this.diacriticmarks[mark][1];
        var imgurl = this.diacriticmarks[mark][0];
        
        var top;
        switch(alignment){
            case 'top':
                top = (loc.y-5);
                break;
            case 'bottom':
                top = (loc.y + loc.height-5);
                break;
            default:
                top = loc.y;
        }
        $('<div></div>').addClass('mark ' + annotation.id).css({
            'top': top,
            'left': loc.x + (0.5 * loc.width) - 5,
            'background-image': 'url(' + imgurl +')',
        }).appendTo('.annotator-wrapper');
    };
    
    /**
     * Gets the Diacritics from the instantiation in studio
     * @returns An object with the diacritics instantiated
     */ 
    Diacritics.prototype.getDiacritics = function(){
        var diacritics = {};
        var diacriticsList;
        if(typeof this.options.diacritics != 'undefined'){
            diacriticsList = this.options.diacritics.split(",");
            $.each(diacriticsList, function(key, item){
                var temp = item.split(";");
                if (temp.length > 2) {
                    diacritics[temp[0]] = [temp[1], temp[2]];
                }
            });
        }
        return diacritics;
    };
    
    /**
     * Gets the position of a specific element given the wrapper
     * @param el {Object} - element you are trying to get the position of
     */
    Diacritics.prototype.getPos = function(el) {
        var element = $(el),
        elementOffset = element.offset(),
        annotatorOffset = $('.annotator-wrapper').offset();

        return {
            x: elementOffset.left - annotatorOffset.left, 
            y: elementOffset.top - annotatorOffset.top, 
            width: element.width(), 
            height: element.height()
        };
    };
    
    /**
     * Redraws the marks above annotations by cycling through tags
     */
    Diacritics.prototype.updateDiacritics = function(){
        $('.mark').remove();
        var annotations = this.annotator.plugins.Store.annotations;
        var self = this;
        $.each(annotations, function(key, annotation){
            $.each(self.diacriticmarks, function(tag){
                if($.inArray(tag, annotation.tags) != -1){
                    self.putMarkAtLocation(annotation, tag); 
                }
            });
        });
    };
    
    /**
     * Removes unnecessary field that Annotator automatically adds to popup
     * @param {Object} field - the html element that represents the popup
     * @param {Object} annotation - the annotation element that holds metadata
     */
    Diacritics.prototype.updateViewer = function(field, annotation){
        $(field).remove();
    };

    /**
     * Function for adding Diacritic choices to the annotator popup
     * @param {Object} field - the html element that represents the popup
     * @param {Object} annotation - the annotation element that holds metadata
     */
    Diacritics.prototype.updateEditorForDiacritics = 
        function(field, annotation){
        
        // if no tags are present, no need to go through this
        if (typeof annotation.tags == 'undefined'){
            return;   
        }
        
        var inputItems = $(this.field).find(':input');
        var dictOfItems = {};
        var self = this;
        
        // add each diacritic mark to a dictionary and default to off
        $.each(inputItems, function(key,item){
            item.checked = false;
            dictOfItems[item.placeholder] = item;
        });

        // match tags to diacritics and check off the ones that are true
        $.each(annotation.tags, function(key,tag){
            if(self.diacriticmarks[tag]){
                dictOfItems[tag].checked = true;
            }
        });
    };
        
    return Diacritics;

})(Annotator.Plugin);
