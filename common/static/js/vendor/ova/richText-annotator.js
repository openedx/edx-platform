/* 
Rich Text Annotator Plugin v1.0 (https://github.com/danielcebrian/richText-annotator)
Copyright (C) 2014 Daniel Cebrian Robles
License: https://github.com/danielcebrian/richText-annotator/blob/master/License.rst

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

Annotator.Plugin.RichText = (function(_super) {

    __extends(RichText, _super);
    
    
    //Default tinymce configuration
    RichText.prototype.options = {
        tinymce:{
            selector: "li.annotator-item textarea",
            skin: 'studio-tmce4',
            formats: {
                code: {
                    inline: 'code'
                }
            },
            codemirror: {
                path: "/static/js/vendor"
            },
            plugins: "image link codemirror media",
            menubar: false,
            toolbar_items_size: 'small',
            extended_valid_elements : "iframe[src|frameborder|style|scrolling|class|width|height|name|align|id]",
            toolbar: "insertfile undo redo | styleselect | bold italic | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | link image media | code ",
            resize: "both",
        }
    };

    function RichText(element,options) {
        _ref = RichText.__super__.constructor.apply(this, arguments);
        return _ref;
    };


    RichText.prototype.pluginInit = function() {
        console.log("RichText-pluginInit");
        var annotator = this.annotator,
            editor = this.annotator.editor;
        // check that annotator is working
        if (!Annotator.supported()) {
            return;
        }
        
        // editor Setup
        annotator.editor.addField({
            type: 'input',
            submit: this.submitEditor,
            load: this.updateEditor,
        });
        
        // viewer setup
        annotator.viewer.addField({
            load: this.updateViewer,
        });
        
        // makes sure that tinymce is hidden and shown along with the editor
        annotator.subscribe("annotationEditorShown", function() {
            $(annotator.editor.element).find('.mce-tinymce')[0].style.display = 'block';
            annotator.editor.checkOrientation();
        });
        annotator.subscribe("annotationEditorHidden", function() {
            $(annotator.editor.element).find('.mce-tinymce')[0].style.display = 'none';
        });
        
        // set listener for tinymce;
        this.options.tinymce.setup = function(ed) {

            // note that the following does not work in Firefox, fix using submitEditor function
            ed.on('change', function(e) {
                // set the modification in the textarea of annotator
                $(editor.element).find('textarea')[0].value = tinymce.activeEditor.getContent();
            });

            // creates a function called whenever editor is resized
            ed.on('init', function(mceInstance) {

                // get win means this event activates when window is resized
                tinymce.dom.Event.bind(ed.getWin(), 'resize', function(e){

                    // mceInstance.target gets the editor, its id is used to retrieved iframe
                    $("#"+mceInstance.target.id+"_ifr").css('min-width', '400px');
                });
            });
            // new button to add Rubrics of the url https://gteavirtual.org/rubric
            ed.addButton('rubric', {
                icon: 'rubric',
                title : 'Insert a rubric',
                onclick: function() {
                    ed.windowManager.open({
                        title: 'Insert a public rubric of the website https://gteavirtual.org/rubric',
                        body: [
                            {type: 'textbox', name: 'url', label: 'Url'}
                        ],
                        onsubmit: function(e) {
                            // Insert content when the window form is submitted
                            var url = e.data.url;
                            var name = 'irb';
                            var irb;
                            // get the variable 'name' from the given url
                            name = name.replace(/[\[]/, "\\\[").replace(/[\]]/, "\\\]");
                            var regex = new RegExp("[\\?&]" + name + "=([^&#]*)");
                            var results = regex.exec(url);
                                
                            // the rubric id
                            irb = results == null ? "" : decodeURIComponent(results[1].replace(/\+/g, " "));
                            if (irb==''){
                                ed.windowManager.alert('Error: The given webpage didn\'t have a irb variable in the url');
                            }else{
                                var iframeRubric = "<iframe src='https://gteavirtual.org/rubric/?mod=portal&scr=viewrb&evt=frame&irb=" + irb + "' style='width:800px;height:600px;overflow-y: scroll;background:transparent' frameborder='0' ></iframe>";
                                ed.setContent(ed.getContent()+iframeRubric);
                                $(editor.element).find('textarea')[0].value = ed.getContent();
                            }
                        }
                    });
                    ed.insertContent('Main button');
                    ed.label = 'My Button';
                }
            });
        };

        // makes sure that if tinymce exists already that this removes/destroys previous version
        if (tinymce.editors.length > 0) {
            tinymce.remove("li.annotator-item textarea");  
        }
        tinymce.init(this.options.tinymce);
    };
    
    /**
     * Copies the content of annotation text and inserts it into the tinymce instance
     */
    RichText.prototype.updateEditor = function(field, annotation) {
        var text = typeof annotation.text != 'undefined' ? annotation.text : '';
        tinymce.activeEditor.setContent(text);
        $(field).remove(); // this is the auto create field by annotator and it is not necessary
    }
    
    /**
     * Takes the text from the annotation text and makes sure it replaces the old text field
     * with the richtext from tinymce. 
     */
    RichText.prototype.updateViewer = function(field, annotation) {
        var textDiv = $(field.parentNode).find('div:first-of-type')[0];
        textDiv.innerHTML = annotation.text;
        $(textDiv).addClass('richText-annotation');
        $(field).remove(); // this is the auto create field by annotator and it is not necessary
    }
    
    /**
     * Gets called before submission. It checks to make sure tinymce content is saved
     */
    RichText.prototype.submitEditor = function(field, annotation) {
        var tinymceText = tinymce.activeEditor.getContent();
        
        // Firefox has an issue where the text is not saved ("on" function doesn't work).
        // this helps save it anyway. 
        if (annotation.text !== tinymceText) {
            annotation.text = tinymce.activeEditor.getContent();
        }
    }
    
    return RichText;

})(Annotator.Plugin);
