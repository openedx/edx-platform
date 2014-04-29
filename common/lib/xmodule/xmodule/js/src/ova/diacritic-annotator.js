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
 
var _ref,
  __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
  __hasProp = {}.hasOwnProperty,
  __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

Annotator.Plugin.Diacritics = (function(_super) {
	__extends(Diacritics, _super);
	
	//Options will include diacritic name, picture used, baseline
    Diacritics.prototype.options = null;
    Diacritics.prototype.diacriticmarks = null;
	
    //initiate diacritics elements
	function Diacritics(element,options) {
		this.pluginSubmit = __bind(this.pluginSubmit, this);
		this.updateDiacritics = __bind(this.updateDiacritics, this);
        this.updateViewer = __bind(this.updateViewer, this);
        this.getDiacritics = __bind(this.getDiacritics, this);
        this.getPos = __bind(this.getPos, this);
        this.putMarkatLocation = __bind(this.putMarkatLocation, this);
        this.updateEditorForDiacritics = __bind(this.updateEditorForDiacritics, this);
        
        this.options = options;
        this.diacriticmarks = this.getDiacritics();
		_ref = Diacritics.__super__.constructor.apply(this, arguments);
		return _ref;
	}
	
    //example variables to be used to receive input in the annotator view
	Diacritics.prototype.field = null;
	Diacritics.prototype.input = null;
    
    //this function will initialize the plug in
    Diacritics.prototype.pluginInit = function() {
		console.log("Diacritics-pluginInit");
		
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
           		    type: 'checkbox', //options (textarea,input,select,checkbox)
    			    label: Annotator._t(item),
    			    submit: self.pluginSubmit,
    		    });
            });
		
    		//-- Viewer
    		var newview = this.annotator.viewer.addField({
    			load: this.updateViewer,
    		});

            this.annotator.subscribe('annotationsLoaded', this.updateDiacritics);
            this.annotator.subscribe('annotationUploaded', this.updateDiacritics);
    		this.annotator.subscribe('annotationDeleted', this.updateDiacritics);
            this.annotator.subscribe('annotationUpdated', this.updateDiacritics);
            this.annotator.subscribe('annotationEditorShown', this.updateEditorForDiacritics, this.field);
            
            var self = this;
            $(window).resize(function() {
                self.updateDiacritics();
            });
        }
        
		return this.input = $(this.field).find(':input');
	};
    
    //The following function is run when a person hits submit.
    Diacritics.prototype.pluginSubmit = function(field, annotation) {
        var checkedItems = $(this.field).find(':input');
        var self = this;
        $.each(checkedItems, function(item){
            if(typeof annotation.tags != 'undefined'){
                var index = $.inArray(checkedItems[item].placeholder, annotation.tags);
                if(index != -1){
                    annotation.tags.splice(index, 1);  
                    if (typeof $($('.annotator-wrapper')[0]).find('div.'+annotation.id)[0] != 'undefined'){
                        $($('.annotator-wrapper')[0]).find('div.'+annotation.id)[0].remove();
                    } else {
                        $($('.annotator-wrapper')[0]).find('div.undefined')[0].remove();   
                    }
                }
               
                if(checkedItems[item].checked == true){
                    annotation.tags.unshift(checkedItems[item].placeholder);
                    self.putMarkatLocation(annotation,  checkedItems[item].placeholder);
                }
            } else {
                if(checkedItems[item].checked == true){
                    annotation['tags'] = [checkedItems[item].placeholder];
                    self.putMarkatLocation(annotation, checkedItems[item].placeholder);
                }
            }
        });
		
    }

    Diacritics.prototype.putMarkatLocation = function (annotation, mark){
        var loc = this.getPos(annotation.highlights[0]);
        var alignment = this.diacriticmarks[mark][1];
        var imgurl = this.diacriticmarks[mark][0];
        
        var newdiv = document.createElement('div');
        var className = 'mark ' + annotation.id;
        newdiv.setAttribute('class',className);
        if(alignment == 'top'){
           $(newdiv).css('top',""+(loc.y-5)+"px");
        } else if(alignment == 'bottom'){
           $(newdiv).css('top',""+(loc.y+loc.height-5)+"px");   
        } else{
           $(newdiv).css('top',""+loc.y+"px");   
        }
        $(newdiv).css('left',""+(loc.x+(loc.width/2.0)-5)+"px");
        $(newdiv).css('background-image', 'url('+imgurl+')');
        $('.annotator-wrapper')[0].appendChild(newdiv);
    }
        
    Diacritics.prototype.getDiacritics = function(){
        if(typeof this.options.diacritics != 'undefined'){
            var self = this;
            var final = new Object(), prelim = this.options.diacritics.split(",");
            prelim.forEach(function(item){
                var temp = item.split(";");
                if (temp.length <3) {return undefined;}
                final[temp[0]] = [temp[1],temp[2]];
            });
            return final;
        }
        console.log("Was undefined");
        return undefined;
    }
    
    Diacritics.prototype.getPos = function(el) {
        var off = $(el).offset();
        return {x: off.left-$($('.annotator-wrapper')[0]).offset().left, y: off.top-$($('.annotator-wrapper')[0]).offset().top, width:$(el).width(), height:$(el).height()};
    }
    
    Diacritics.prototype.updateDiacritics = function(){
        $('.mark').remove();
        var annotations = this.annotator.plugins['Store'].annotations;
        var self = this;
        annotations.forEach(function(ann){
            $.each(self.diacriticmarks, function(item){
                if($.inArray(item, ann.tags) != -1){
                    self.putMarkatLocation(ann, item); 
                }
            });
        });
    }
    
    Diacritics.prototype.updateViewer = function(field,annotation){
        $(field).remove();
    }
    
    Diacritics.prototype.updateEditorForDiacritics = function(field, annotation){
        if (typeof annotation.tags == 'undefined'){
            return;   
        }
        var self = this;
        
        var inputItems = $(this.field).find(':input');
        var dictOfItems = {}
        $.each(inputItems, function(item){
            inputItems[item].checked = false;
            dictOfItems[inputItems[item].placeholder] = inputItems[item];
        });
        annotation.tags.forEach(function(tag){
            if(typeof self.diacriticmarks[tag] != 'undefined'){
                dictOfItems[tag].checked = true;
            }
        });
    }
    
    
    
    return Diacritics;

})(Annotator.Plugin);