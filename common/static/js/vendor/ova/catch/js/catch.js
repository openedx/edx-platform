/* 
Grid Annotation Plugin v1.0
Copyright (C) 2014 Daniel Cebrian Robles and Luis Duarte
License: https://github.com/danielcebrian/share-annotator/blob/master/License.rst

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
// The name of the plugin that the user will write in the html
window.CatchAnnotation = ("CatchAnnotation" in window) ? CatchAnnotation : {};
window.CatchSources = ("CatchSources" in window) ? CatchSources : {};


//    
//     HTML TEMPLATES
// 
CatchSources.HTMLTEMPLATES = function(root){
    var root = root || '';
    return {
// Main
annotationList:
    '<div class="annotationListButtons">'+
        '{{{ PublicPrivate }}}'+
    '</div>'+
    '<div class="annotationList">'+
        '{{{ MediaSelector }}}'+
        '<div class="header">'+
            '<div class="annotationRow">'+
                '<div class="expandableIcon field">'+
                    '&nbsp  <!-- TODO: better way to ensure width upon hide -->'+
                '</div>'+

                '<div class="annotatedBy field">'+
                    gettext('User')+
                '</div>'+

                '<div class="body field">'+
                    gettext('Annotation')+
                '</div>'+  
                
                '{{#if videoFormat}}'+
                    '<div class="start field">'+
                        gettext('Start')+
                    '</div>'+

                    '<div class="end field">'+
                        gettext('End')+
                    '</div>'+
                '{{/if}}'+
                
                '<div class="totalreplies field">'+
                    gettext('#Replies')+
                '</div>'+
                
                '<div class="annotatedAt field">'+
                    gettext('Date posted')+
                '</div>'+
            '</div>'+
        '</div>'+
        '{{#each annotationItems}}'+
            '{{{ this }}}'+
        '{{/each}}'+
    '</div>'+
    '<div class="annotationListButtons">'+
        '<div class="moreButtonCatch">'+gettext('More')+'</div>'+
    '</div>',
    
// Main->PublicPrivateInstructor
annotationPublicPrivateInstructor:
    '<div class="selectors"><div class="PublicPrivate myNotes active">'+gettext('My Notes')+'<span class="action">myNotes</span></div>'+ 
    '<div class="PublicPrivate instructor"> '+gettext('Instructor')+'<span class="action">instructor</span></div>'+
    '<div class="PublicPrivate public"> '+gettext('Public')+'<span class="action">public</span></div></div>'+
    '<div class="searchbox"><div class="searchinst">'+gettext('Search')+'</div><select class="dropdown-list">'+
    '<option>'+gettext('Users')+'</option>'+
    '<option>'+gettext('Tags')+'</option>'+
    '<option>'+gettext('Annotation Text')+'</option>'+
    '</select><input type="text" name="search"/><div class="search-icon" alt="Run search."></div><div class="clear-search-icon" alt="Clear search.">'+gettext('Clear')+'</div></div>',
    
// Main->PublicPrivate
annotationPublicPrivate:
    '<div class="selectors"><div class="PublicPrivate myNotes active">'+gettext('My Notes')+'<span class="action">myNotes</span></div>'+ 
    '<div class="PublicPrivate public"> '+gettext('Public')+'<span class="action">public</span></div></div>'+
    '<div class="searchbox"><div class="searchinst">'+gettext('Search')+'</div><select class="dropdown-list">'+
    '<option>'+gettext('Users')+'</option>'+
    '<option>'+gettext('Tags')+'</option>'+
    '<option>'+gettext('Annotation Text')+'</option>'+
    '</select><input type="text" name="search"/><div class="search-icon" alt="Run search."></div><div class="clear-search-icon" alt="Clear search.">'+gettext('Clear')+'</div></div>',
    
// Main->MediaSelector
annotationMediaSelector:
    '<ul class="ui-tabs-nav">'+
        '<li class="ui-state-default" media="text">'+
            gettext('Text')+
        '</li>'+
        '<li class="ui-state-default" media="video">'+
            gettext('Video')+
        '</li>'+
        '<li class="ui-state-default" media="image">'+
            gettext('Image')+
        '</li>'+
    '</ul>',

// Main->ContainerRow
annotationItem: 
    '<div class="annotationItem {{ evenOrOdd }} {{ openOrClosed }}" annotationId="{{ id }}">'+
        '{{{ annotationRow }}}'+
        '{{{ annotationDetail }}}'+
    '</div>',

// Main->ContainerRow->Reply
annotationReply: 
    '{{#if annotations}}'+
        '{{#each annotations}}'+
            '<blockquote class="replyItem" annotationId="{{this.id}}" style="font-size:90%">'+
                '<p>'+
                    'On  {{ this.updated }} <!--<a href="index.php?r=user/user/view&id={{{this.user.id}}}">-->{{{ this.user.name }}}<!--</a>-->{{#if this.geolocation}}, wrote from {{/if}}'+
                    '{{#if geolocation}}'+
                    '<span class="geolocationIcon">'+
                        '<img src="'+root+'geolocation_icon.png"width="25" height="25" alt="Location Map" title="Show Location Map" data-dropdown="myLocationMap"/>'+
                        '<span class="idAnnotation" style="display:none">{{{ this.id }}}</span>'+
                        '<span class="latitude" style="display:none">{{{ this.geolocation.latitude }}}</span>'+
                        '<span class="longitude" style="display:none">{{{ this.geolocation.longitude }}}</span>'+
                    '</span>'+
                    '<div id="myLocationMap" data-dropdown-content class="f-dropdown content">'+
                        '<div class="map"></div>'+
                    '</div>'+
                    '{{/if}}'+
                    '<div class="deleteReply">'+gettext('Delete')+'</div>'+
                '</p>'+
                '<p>'+
                    '{{#if this.text}}'+
                        '{{{this.text}}}'+
                     '{{else}}'+
                        '-'+
                    '{{/if}}'+
                '</p>'+
            '</blockquote>'+
        '{{/each}}'+
    '{{/if}}',

// Main->ContainerRow->Row
annotationRow:
    '<div class="annotationRow item">'+
        '<div class="expandableIcon field">'+
            '<img src="'+root+'expandableIcon.png" alt="View Details" />'+
            '&nbsp'+
        '</div>'+

        '<div class="annotatedBy field">'+
            '{{ user.name }}'+
        '</div>'+

        '<div class="body field">'+
            '{{#if plainText}}'+
                '{{deparagraph plainText}}'+
             '{{else}}'+
                '-'+
            '{{/if}}'+
        '</div>'+

        '<div class="start field">'+
            '{{ rangeTime.start }}'+
        '</div>'+

        '<div class="end field">'+
            '{{ rangeTime.end }}'+
        '</div>'+
        
        '<div class="totalreplies field">'+
            '{{ totalComments }}'+
        '</div>'+

        '<div class="annotatedAt field">'+
            '{{ updated }}'+
        '</div>'+
    '</div>',

// Main->ContainerRow->DetailRow
annotationDetail:
    '{{#if mediatypeforgrid.text}}'+
      '<div class="annotationDetail">'+
    '{{/if}}'+
    '{{#if mediatypeforgrid.video}}'+
        '<div class="annotationDetail videoAnnotationDetail">'+
    '{{/if}}'+
    '{{#if mediatypeforgrid.image}}'+
        '<div class="annotationDetail imageAnnotationDetail">'+
    '{{/if}}'+
        '<div class="detailHeader">'+
            '<span class="closeDetailIcon">'+
                '<img src="'+root+'closeIcon.png" alt="Hide Details" />'+
            '</span>'+
            'On  {{ updated }} <!--<a href="index.php?r=user/user/view&id={{{user.id}}}">-->{{{ user.name }}}<!--</a>-->{{#if geolocation}}, wrote from {{/if}}'+
            '{{#if geolocation}}'+
            '<span class="geolocationIcon">'+
                '<img src="'+root+'geolocation_icon.png"width="25" height="25" alt="Location Map" title="Show Location Map" data-dropdown="myLocationMap"/>'+
                '<span class="idAnnotation" style="display:none">{{{ id }}}</span>'+
                '<span class="latitude" style="display:none">{{{ geolocation.latitude }}}</span>'+
                '<span class="longitude" style="display:none">{{{ geolocation.longitude }}}</span>'+
            '</span>'+
            '<div id="myLocationMap" data-dropdown-content class="f-dropdown content">'+
                '<div class="map"></div>'+
            '</div>'+
            '{{/if}}'+
        '</div>'+

    '{{#if mediatypeforgrid.text}}'+
        '<div class="quote">'+
            '<div style="text-align: center">'+
            '<div class="quoteItem">“</div><div class="quoteText">{{{ quote }}}</div><div class="quoteItem">”</div></div>'+
            '<span class="idAnnotation" style="display:none">{{{ id }}}</span>'+
            '<span class="uri" style="display:none">{{{uri}}}</span>'+
        '</div>'+
    '{{/if}}'+
    '{{#if mediatypeforgrid.video}}'+
        '<div class="playMediaButton">'+
            'Play segment {{{ rangeTime.start }}} - {{{ rangeTime.end }}}'+
            '<span class="idAnnotation" style="display:none">{{{ id }}}</span>'+
            '<span class="uri" style="display:none">{{{uri}}}</span>'+
            '<span class="container" style="display:none">{{{target.container}}}</span>'+
        '</div>'+
    '{{/if}}'+
    '{{#if mediatypeforgrid.image}}'+
        '<div class="zoomToImageBounds">'+
            '<img src="{{{ thumbnailLink }}}">'+
            '<span class="idAnnotation" style="display:none">{{{ id }}}</span>'+
            '<span class="uri" style="display:none">{{{uri}}}</span>'+
        '</div>'+
    '{{/if}}'+
        '<div class="body">'+
            '{{{ text }}}'+
        '</div>'+

        '<div class="controlReplies">'+
            '<div class="newReply" style="text-decoration:underline">'+gettext('Reply')+'</div>&nbsp;'+
            '<div class="hideReplies" style="text-decoration:underline;display:{{#if hasReplies}}block{{else}}none{{/if}}">Show Replies</div>&nbsp;'+
            '{{#if authToEditButton}}'+
                '<div class="editAnnotation" style="text-decoration:underline">'+gettext('Edit')+'</div>'+
            '{{/if}}'+
            '{{#if authToDeleteButton}}'+
                '<div class="deleteAnnotation" style="text-decoration:underline">'+gettext('Delete')+'</div>'+
            '{{/if}}'+
        '</div>'+
        
        '<div class="replies"></div>'+
        
        
    '{{#if tags}}'+
        '<div class="tags">'+
            '<h3>'+gettext('Tags:')+'</h3>'+
            '{{#each tags}}'+
                '<div class="tag">'+
                    '{{this}}'+
                '</div>'+
            '{{/each}}'+
        '</div>'+
    '{{/if}}'+

        '<div class="controlPanel">'+
        '</div>'+
    '</div>',
};
};



CatchAnnotation = function (element, options) {
    // local variables
    var $ = jQuery,
        options = options || {};

    // Options
    var defaultOptions = {
        media: 'text',
        userId: '', // this is an integer and its value is the userId to see user annotations
        externalLink: false, // This is true if you want to open the link in a new URL. However, it is false if you want to open the url in the same page
        showMediaSelector: true, // whether show the selector of Media Annotations or not
        showPublicPrivate: true, // Whether show Public or Private Annotation Selector
        pagination: 50, // Number of Annotations per load in the pagination
        flags:false // This checks to see if user is staff and has access to see flags
    };
    this.options = $.extend( true, defaultOptions, options );
    
    // element
    this.element = element;
    
    // clean boolean
    this.clean = false;
    
    // Reset element an create a new element div
    element.html('<div id="mainCatch" class="annotationListContainer"></div>');
    this.current_tab = this.options.default_tab;
    // INIT
    var self = this;
    $( document ).ready(function() {
        self.init();
        self.refreshCatch(true);
        var moreBut = self.element.find('.annotationListButtons .moreButtonCatch');
        moreBut.hide(); 
    });
    
    return this;
}

CatchAnnotation.prototype = {
    init: function(){
        // Set variables
        // Initial Templates
        this.TEMPLATENAMES = [
            "annotationList", // Main
            "annotationPublicPrivate", // Main->PublicPrivate
            "annotationPublicPrivateInstructor", // Main->PublicPrivateInstructor
            "annotationMediaSelector", // Main->MediaSelector
            "annotationItem", // Main->ContainerRow
            "annotationReply", // Main->ContainerRow->Reply
            "annotationRow", // Main->ContainerRow->Row
            "annotationDetail", // Main->ContainerRow->DetailRow
        ];
        // annotator
        var wrapper = $('.annotator-wrapper').parent()[0];
        var annotator = $.data(wrapper, 'annotator');
        this.annotator = annotator;
        
        // Subscribe to annotator
        this._subscribeAnnotator();
        
        //    
        //    Handlebars Register Library
        // 
        Handlebars.registerHelper('deparagraph', function(txt) {
            var dpg = txt.replace("<p>", "").replace("</p>", "");
            return dpg;
        });
        
        // Compile templates
        this.HTMLTEMPLATES = CatchSources.HTMLTEMPLATES(this.options.imageUrlRoot);
        this.TEMPLATES = {};
        this._compileTemplates();
        
        // the default annotations are the user's personal ones instead of instructor.
        // if the default tab is instructor, we must refresh the catch to pull the ones
        // under the instructor's email. Calling changeUserId will update this.options.userId
        // and most importantly refresh not only the highlights (from Annotator) 
        // but also the table below from the annotations database server (called Catch).
        if(this.options.default_tab.toLowerCase() === 'instructor') {
            this.changeUserId(this.options.instructor_email);
        }
    },
//    
//     GLOBAL UTILITIES
// 
    getTemplate: function(templateName) {
        return this.TEMPLATES[templateName]() || '';
    },
    refreshCatch: function(newInstance) {
        var mediaType = this.options.media || 'text';
        var annotationItems = [];
        var index = 0;
        var annotations = this.annotator.plugins['Store'].annotations || [];
        var el = $("#mainCatch.annotationListContainer");
        var self = this;
        var newInstance = newInstance || false;
        annotations.forEach(function(annotation) {
            var isMedia = annotation.media === self.options.media;
            var isUser = (typeof self.options.userId !== 'undefined' && self.options.userId !== '' && self.options.userId !== null)?
                    self.options.userId === annotation.user.id:true;
            var isInList = newInstance?false:self._isInList(annotation);
            if (isMedia && isUser && !isInList) {
                var item = jQuery.extend(true, {}, annotation);
                self._formatCatch(item);
                
                // Authorized
                var permissions = self.annotator.plugins.Permissions;
                var authorized = permissions.options.userAuthorize('delete', annotation, permissions.user);
                var updateAuthorized = permissions.options.userAuthorize('update', annotation, permissions.user);
                
                item.authToDeleteButton = authorized;
                item.authToEditButton = updateAuthorized;
                item.hasReplies = (item.totalComments > 0);
                var html = self.TEMPLATES.annotationItem({
                    item: item,
                    id: item.id,
                    evenOrOdd: index % 2 ? "odd" : "even",
                    openOrClosed: "closed",
                    annotationRow: self.TEMPLATES.annotationRow(item),
                    annotationDetail: self.TEMPLATES.annotationDetail(item),
                });
                index++;
                annotationItems.push(html);
            }
        });
        
        if (newInstance) {
            var videoFormat = (mediaType === "video") ? true : false;
            var publicPrivateTemplate = '';
            if (self.options.showPublicPrivate) {
                var templateName = this.options.instructor_email ? 
                    "annotationPublicPrivateInstructor" : 
                    "annotationPublicPrivate";
            }
            el.html(self.TEMPLATES.annotationList({ 
                annotationItems: annotationItems, 
                videoFormat: videoFormat,
                PublicPrivate: this.getTemplate(templateName),
                MediaSelector: self.options.showMediaSelector?self.TEMPLATES.annotationMediaSelector():'',
            }));
        } else {
            var list = $("#mainCatch .annotationList");
            annotationItems.forEach(function(annotation) {
                list.append($(annotation));
            });
        }
        
        // Set SelButtons to media
        var SelButtons = el.find('.annotationList li').removeClass('active'); // reset
        for (var index=0;index<SelButtons.length;index++) {
            var span = $(SelButtons[index]);
            if (span.attr("media") === this.options.media) $(SelButtons[index]).addClass('active');
        }
        // Set PublicPrivate
        var PublicPrivateButtons = el.find('.annotationListButtons .PublicPrivate').removeClass('active'); // reset
        for (var index=0;index<PublicPrivateButtons.length;index++) {
            var span = $(PublicPrivateButtons[index]).find('span');
            if (span.html().toLowerCase() === self.current_tab.toLowerCase()) {
                switch (self.current_tab.toLowerCase()){
                    case 'public':
                        self.options.userId = '';
                        break;
                    case 'instructor':
                        self.options.userId = this.options.instructor_email;
                        break;
                    default:
                        self.options.userId = this.annotator.plugins.Permissions.user.id;
                        break;
                }
                $(PublicPrivateButtons[index]).addClass('active');
            }
        }
        
        // reset all old events
        el.off();
        
        // Bind functions
        var openAnnotationItem = this.__bind(this._openAnnotationItem, this);
        var closeAnnotationItem = this.__bind(this._closeAnnotationItem, this);
        var onGeolocationClick = this.__bind(this._onGeolocationClick, this);
        var onPlaySelectionClick = this.__bind(this._onPlaySelectionClick, this);
        var onShareControlsClick = this.__bind(this._onShareControlsClick, this);
        var onSelectionButtonClick = this.__bind(this._onSelectionButtonClick, this);
        var onPublicPrivateButtonClick = this.__bind(this._onPublicPrivateButtonClick, this);
        var onQuoteMediaButton = this.__bind(this._onQuoteMediaButton, this);
        var onControlRepliesClick = this.__bind(this._onControlRepliesClick, this);
        var onMoreButtonClick = this.__bind(this._onMoreButtonClick, this);
        var onSearchButtonClick = this.__bind(this._onSearchButtonClick, this);
        var onClearSearchButtonClick = this.__bind(this._onClearSearchButtonClick, this);
        var onDeleteReplyButtonClick = this.__bind(this._onDeleteReplyButtonClick, this);
        var onZoomToImageBoundsButtonClick = this.__bind(this._onZoomToImageBoundsButtonClick, this);
        var openLoadingGIF = this.__bind(this.openLoadingGIF, this);
        //Open Button
        el.on("click", ".annotationItem .annotationRow", openAnnotationItem);
        // Close Button
        el.on("click", ".annotationItem .detailHeader", closeAnnotationItem);
        // Geolocation button
        el.on("click", ".annotationItem .detailHeader .geolocationIcon img", onGeolocationClick);
        // controlPanel buttons
        el.on("click", ".annotationItem .annotationDetail .controlPanel", onShareControlsClick);
        // VIDEO
        if (this.options.media === 'video') {
            // PlaySelection button
            el.on("click", ".annotationItem .annotationDetail .playMediaButton", onPlaySelectionClick);
        }
        // TEXT
        if (this.options.media === 'text') {
            // PlaySelection button
            el.on("click", ".annotationItem .annotationDetail .quote", onQuoteMediaButton);
        }

        // IMAGE
        if (this.options.media === 'image') {
            // PlaySelection button
            el.on("click", ".annotationItem .annotationDetail .zoomToImageBounds", onZoomToImageBoundsButtonClick);
        }
        
        // controlReplies
        el.on("click", ".annotationItem .controlReplies", onControlRepliesClick);
        
        // Selection Buttons
        el.on("click", ".annotationList li", onSelectionButtonClick);
        // PublicPrivate Buttons
        el.on("click", ".annotationListButtons .PublicPrivate", onPublicPrivateButtonClick);
        // More Button
        el.on("click", ".annotationListButtons .moreButtonCatch", onMoreButtonClick);
        
        // Search Button
        el.on("click", ".searchbox .search-icon", onSearchButtonClick);

        // Clear Search Button
        el.on("click", ".searchbox .clear-search-icon", onClearSearchButtonClick);
        
        // Delete Reply Button
        el.on("click", ".replies .replyItem .deleteReply", onDeleteReplyButtonClick);
        
        el.on("click", ".annotationListButtons .PublicPrivate", openLoadingGIF);
    },
    changeMedia: function(media) {
        var media = media || 'text';
        this.options.media = media;
        this._refresh();
        this.refreshCatch(true);
        this.checkTotAnnotations();
    },
    changeUserId: function(userId) {
        var userId = userId || '';
        this.options.userId = userId;
        this._refresh();
        this.refreshCatch(true);
        this.checkTotAnnotations();
    },
    
    /**
     * This function makes sure that the annotations loaded are only the ones that we are
     * currently looking for. Annotator has a habit of loading the user's annotations
     * immediately without checking to see if we are doing some filtering or otherwise.
     * Since it's a vendor file, this is the workaround for that bug.
     */
    cleanUpAnnotations: function(){
        var annotator = this.annotator;
        var store = annotator.plugins.Store;
        var annotations = store.annotations;
        var self = this;
        
        // goes through all the annotations currently loaded
        $.each(annotations, function(key, value){
            // if the options.userID (i.e. the value we are searching for) is empty signifying
            // public or is equal to the person with update access, then we leave it alone,
            // otherwise we need to clean them up (i.e. disable them).
            if (self.options.userId !== '' && self.options.userId !== value.permissions.update[0]) {
                if (value.highlights !== undefined) {
                    $.each(value.highlights, function(key1, value1){
                        $(value1).removeClass('annotator-hl');
                    });
                }
            }
        });
    },
    loadAnnotations: function() {
        var annotator = this.annotator;
        var loadFromSearch = annotator.plugins.Store.options.loadFromSearch;
        var loadedAn = this.element.find('.annotationList .annotationItem').length;
        loadedAn = typeof loadedAn !== 'undefined' ?loadedAn:0;
        
        loadFromSearch.limit = this.options.pagination;
        loadFromSearch.offset = loadedAn;
        loadFromSearch.media = this.options.media;
        loadFromSearch.userid = this.options.userId;
        
        // Dani had this for some reason. we can't remember. but if something
        // breaks, uncomment next line.
        // annotator.plugins['Store'].loadAnnotationsFromSearch(loadFromSearch);
        
        // Make sure to be openned all annotations for this pagination
        loadFromSearch.limit = this.options.pagination+loadedAn;
        loadFromSearch.offset = 0;
        annotator.plugins['Store'].loadAnnotationsFromSearch(loadFromSearch);
        
        // text loading annotations
        var moreBut = this.element.find('.annotationListButtons .moreButtonCatch');
        moreBut.html('Please wait, loading...');
    },
            
    // check whether is necessary to have a more button or not
    checkTotAnnotations: function() {
        var annotator = this.annotator;
        var loadFromSearch = annotator.plugins.Store.options.loadFromSearch;
        var oldLimit = loadFromSearch.limit;
        var oldOffset = loadFromSearch.offset;
        var self = this;
            
        loadFromSearch.limit = 0;
        loadFromSearch.offset = 0;
        loadFromSearch.media = this.options.media;
        loadFromSearch.userid = this.options.userId;
        var onSuccess = function(response) {
            var totAn = self.element.find('.annotationList .annotationItem').length;
            var maxAn = response.total;
            var moreBut = self.element.find('.annotationListButtons .moreButtonCatch');
            if (totAn<maxAn && totAn > 0)
                moreBut.show();
            else
                moreBut.hide();
        }
        
        var obj = loadFromSearch;
        var action = 'search';
    
        var id, options, url;
        id = obj && obj.id;
        url = annotator.plugins['Store']._urlFor(action, id);
        options = annotator.plugins['Store']._apiRequestOptions(action, obj, onSuccess);
        $.ajax(url, options);
        
        // reset values
        loadFromSearch.limit = oldLimit;
        loadFromSearch.offset = oldOffset;
        
        // set More button text
        var moreBut = this.element.find('.annotationListButtons .moreButtonCatch');
        moreBut.html('More');
        
    },

//    
//     LOCAL UTILITIES
// 
    _subscribeAnnotator: function() {
        var self = this;
        var annotator = this.annotator;
        // Subscribe to Annotator changes
        annotator.subscribe("annotationsLoaded", function (annotations) {
            self.cleanUpAnnotations();
            self.refreshCatch(self.clean);
            // hide or show more button
            self.checkTotAnnotations();
        });
        annotator.subscribe("annotationUpdated", function (annotation) {
            self.refreshCatch(true);
            self.checkTotAnnotations();
        });
        annotator.subscribe("annotationDeleted", function (annotation) {
            var annotations = annotator.plugins['Store'].annotations;
            var tot = typeof annotations !== 'undefined' ?annotations.length : 0;
            var attempts = 0; // max 100
            if(annotation.media === "image") {
                self.refreshCatch(true);
                self.checkTotAnnotations();
            } else {
            // This is to watch the annotations object, to see when is deleted the annotation
                var ischanged = function() {
                    var new_tot = annotator.plugins['Store'].annotations.length;
                    if (attempts<100)
                        setTimeout(function() {
                            if (new_tot !== tot) {
                                self.refreshCatch(true);
                                self.checkTotAnnotations();
                            } else {
                                attempts++;
                                ischanged();
                            }
                        }, 100); // wait for the change in the annotations
                };
                ischanged();
            }
        });
        annotator.subscribe("annotationCreated", function (annotation) {
            var attempts = 0; // max 100
            // There is a delay between calls to the backend--especially reading after
            // writing. This function listens to when a function is created and waits
            // until the server provides it with an annotation id before doing anything
            // with it. 
            var ischanged = function(){
                if (attempts<100)
                    setTimeout(function() {
                        if (typeof annotation.id !== 'undefined'){
                        
                            // once it gets the annotation id, the table refreshes to show
                            // the edits
                            self.refreshCatch();
                            if (typeof annotation.parent !== 'undefined' && annotation.parent !== '0'){
                                
                                // if annotation made was actually a replay to an annotation
                                // i.e. the only difference is that annotations that are
                                // not replies have no "parent"
                                var replies = $("[annotationid="+annotation.parent+"]").find(".controlReplies .hideReplies");
                                
                                // forces "Show replies" section to show and then refreshes
                                // via two clicks
                                replies.show();
                                replies.click();
                                replies.click();
                            }
                        } else {
                            attempts++;
                            ischanged();
                        }
                    }, 100); // wait for annotation id
            };
            ischanged();
        });
    },
    __bind: function(fn, me) { return function(){ return fn.apply(me, arguments); }; },
    _compileTemplates: function() {
        var self = this;
        // Change the html tags to functions 
        this.TEMPLATENAMES.forEach(function(templateName) {
            self.TEMPLATES[templateName] = Handlebars.compile(self.HTMLTEMPLATES[templateName]);
        });
    },
    _isVideoJS: function (an) {
        var annotator = this.annotator;
        var rt = an.rangeTime;
        var isOpenVideojs = (typeof annotator.mplayer !== 'undefined');
        var isVideo = (typeof an.media !== 'undefined' && an.media === 'video');
        var isNumber = (typeof rt !== 'undefined' && !isNaN(parseFloat(rt.start)) && isFinite(rt.start) && !isNaN(parseFloat(rt.end)) && isFinite(rt.end));
        return (isOpenVideojs && isVideo && isNumber);
    },
    _isInList: function (an){
        var annotator = this.annotator;
        var isInList = false;
        var list = $('#mainCatch .annotationList .annotationRow.item');
        for (_i = 0, _len = list.length; _i < _len; _i++) {
             if (parseInt($(list[_i]).parent().attr('annotationid'), 10) === an.id)
                  isInList = true;
        }
        return isInList;
    },
    _formatCatch: function(item) {
        var item = item || {};
        
        if (this._isVideoJS(item)) {
            // format time
            item.rangeTime.start= typeof vjs !== 'undefined' ?
                vjs.formatTime(item.rangeTime.start) :
                item.rangeTime.start;
            item.rangeTime.end= typeof vjs !== 'undefined'?
                vjs.formatTime(item.rangeTime.end) :
                item.rangeTime.end;
        }
        // format date
        if (typeof item.updated !== 'undefined' && typeof createDateFromISO8601 !== 'undefined')
            item.updated = createDateFromISO8601(item.updated);
        // format geolocation
        if (typeof item.geolocation !== 'undefined' && (typeof item.geolocation.latitude === 'undefined' || item.geolocation.latitude === ''))
            delete item.geolocation;
        
        /* NEW VARIABLES */
        // set plainText for Catch
        item.plainText = item.text.replace(/&(lt|gt);/g, function (strMatch, p1){
            return (p1 === "lt")? "<" : ">";
        }); // Change to < and > tags
        item.plainText = item.plainText.replace(/<\/?[^>]+(>|$)/g, "").replace('&nbsp;', ''); // remove all the html tags
        
        item.mediatypeforgrid = {};
        item.mediatypeforgrid[item.media] = true;

        if (item.mediatypeforgrid.image) {
            item.thumbnailLink = item.target.thumb;
        };

        // Flags
        if (!this.options.flags && typeof item.tags !== 'undefined' && item.tags.length > 0) {
            for (var len = item.tags.length, index = len-1; index >= 0; --index) {
                var currTag = item.tags[index];
                if (currTag.indexOf("flagged-") !== -1) {
                    item.tags.splice(index);
                }
            }
        }
    },
    
//    
//     EVENT HANDLER
// 
    _openAnnotationItem: function(evt) {
        var isClosed = $(evt.currentTarget).closest(".annotationItem").hasClass("closed");
        if (isClosed) {
            $(evt.currentTarget).closest(".annotationItem").removeClass("closed").addClass("open");
            // Add Share button
            var shareControl = $(evt.currentTarget).closest(".annotationItem").find('.annotationDetail .controlPanel:first'),
                annotator = this.annotator,
                idAnnotation = shareControl.parent().find('.idAnnotation').html(),
                uri = shareControl.parent().find('.uri').html();
            // remove the last share container
            shareControl.find('.share-container-annotator').remove();
            shareControl.append(annotator.plugins.Share.buildHTMLShareButton("", idAnnotation));
            // Set actions button
            annotator.plugins.Share.buttonsActions(shareControl[0], 1, uri);
        } else {
            $(evt.currentTarget).closest(".annotationItem").removeClass("open").addClass("closed");
        }
    },
   _closeAnnotationItem: function(evt) {
        var existEvent = typeof evt.target !== 'undefined' && typeof evt.target.localName !== 'undefined';
        if (existEvent && evt.target.parentNode.className !== 'geolocationIcon') {
            this._openAnnotationItem(evt);
        }
   },
   _onGeolocationClick: function(evt) {
        var latitude = $(evt.target).parent().find('.latitude').html();
        var longitude = $(evt.target).parent().find('.longitude').html();
        var imgSrc = '<img src="http://maps.googleapis.com/maps/api/staticmap?center=' + latitude + ',' + longitude + '&zoom=14&size=500x500&sensor=false&markers=color:green%7Clabel:G%7C' + latitude + ',' + longitude + '">';
        $(evt.target).parents('.detailHeader:first').find('#myLocationMap .map').html(imgSrc);
    },
    _onPlaySelectionClick: function(evt) {
        var id = parseInt($(evt.target).find('.idAnnotation').html(), 10);
        var uri = $(evt.target).find('.uri').html();
        var container = $(evt.target).find('.container').html();
        if (this.options.externalLink) {
            uri += (uri.indexOf('?') >= 0) ? '&ovaId=' + id : '?ovaId=' + id;
            location.href = uri;
        } else {
            var isContainer = typeof this.annotator.an !== 'undefined' && typeof this.annotator.an[container] !== 'undefined';
            var ovaInstance = isContainer ? this.annotator.an[container] : null;
            if (ovaInstance !== null) {
                var allannotations = this.annotator.plugins['Store'].annotations,
                    ovaId = id,
                    player = ovaInstance.player;

                for (var item in allannotations) {
                    var an = allannotations[item];
                    if (typeof an.id !== 'undefined' && an.id === ovaId) { // this is the annotation
                        if (this._isVideoJS(an)) { // It is a video
                            if (player.id_ === an.target.container && player.tech.options_.source.src === an.target.src) {
                                var anFound = an;

                                var playFunction = function(){
                                    // Fix problem with youtube videos in the first play. The plugin don't have this trigger
                                    if (player.techName === 'Youtube') {
                                        var startAPI = function() {

                                            ovaInstance.showAnnotation(anFound);
                                        }
                                        if (ovaInstance.loaded)
                                            startAPI();
                                        else
                                            player.one('loadedRangeSlider', startAPI); // show Annotations once the RangeSlider is loaded
                                    } else {

                                        ovaInstance.showAnnotation(anFound);
                                    }

                                    $('html, body').animate({
                                        scrollTop: $("#" + player.id_).offset().top},
                                        'slow');
                                };
                                if (player.paused()) {
                                    player.play();
                                    player.one('playing', playFunction);
                                } else {
                                    playFunction();
                                }

                                return false; // this will stop the code to not set a new player.one.
                            }
                        }
                    }
                }
            }
        }
    },
    _onZoomToImageBoundsButtonClick: function(evt){
        var zoomToBounds = $(evt.target).hasClass('zoomToImageBounds')?$(evt.target):$(evt.target).parents('.zoomToImageBounds:first');
        var osdaId = parseInt(zoomToBounds.find('.idAnnotation').html(), 10);
        var uri = zoomToBounds.find('.uri').html();

        var allannotations = this.annotator.plugins['Store'].annotations;
        var osda = this.annotator.osda;

        if (this.options.externalLink) {
            uri += (uri.indexOf('?') >= 0) ?'&osdaId=' + osdaId : '?osdaId=' + osdaId;
            location.href = uri;
        }
        for(var item in allannotations) {
            var an = allannotations[item];
            // Makes sure that all images are set to transparent in case one was
            // previously selected.
            an.highlights[0].style.background = "rgba(0, 0, 0, 0)";
            if (typeof an.id !== 'undefined' && an.id === osdaId) { // this is the annotation
                var bounds = new OpenSeadragon.Rect(an.bounds.x, an.bounds.y, an.bounds.width, an.bounds.height);
                osda.viewer.viewport.fitBounds(bounds, false);

                $('html, body').animate({scrollTop: $("#"+an.target.container).offset().top},
                                        'slow');
                // signifies a selected annotation once OSD has zoomed in on the
                // appropriate area, it turns the background a bit yellow
                an.highlights[0].style.background = "rgba(255, 255, 10, 0.2)";
            }
        }
    },
    _onQuoteMediaButton: function(evt) {
        var quote = $(evt.target).hasClass('quote')?$(evt.target):$(evt.target).parents('.quote:first');
        var id = parseInt(quote.find('.idAnnotation').html(), 10);
        var uri = quote.find('.uri').html();
        if (typeof id === 'undefined' || id === ''){
            this.refreshCatch();
            this.checkTotAnnotations();
            id = quote.find('.idAnnotation').html();
            // clickPlaySelection(evt);
        }
        if (this.options.externalLink) {
            uri += (uri.indexOf('?') >= 0)?'&ovaId='+id:'?ovaId='+id;
            location.href = uri;
        } else {
            var allannotations = this.annotator.plugins['Store'].annotations;
            var ovaId = id;
            for (var item in allannotations) {
                var an = allannotations[item];
                if (typeof an.id !== 'undefined' && an.id === ovaId) { // this is the annotation
                    if(!this._isVideoJS(an)) {

                        var hasRanges = typeof an.ranges !== 'undefined' && typeof an.ranges[0] !== 'undefined',
                            startOffset = hasRanges?an.ranges[0].startOffset:'',
                            endOffset = hasRanges?an.ranges[0].endOffset:'';

                        if (typeof startOffset !== 'undefined' && typeof endOffset !== 'undefined') { 

                            $(an.highlights).parent().find('.annotator-hl').removeClass('api'); 
                            // change the color
                            $(an.highlights).addClass('api'); 
                            // animate to the annotation
                            $('html, body').animate({
                                scrollTop: $(an.highlights[0]).offset().top},
                                'slow');
                        }
                    }
                }
            }
        }
    },
    _refreshReplies: function(evt) {
        var item = $(evt.target).parents('.annotationItem:first');
        var anId = parseInt(item.attr('annotationId'), 10);
            
        var replyElem = $(evt.target).parents('.annotationItem:first').find('.replies');
        var annotator = this.annotator;
        var loadFromSearchURI = annotator.plugins.Store.options.loadFromSearch.uri;
        var self = this;
        var action='search';
        var loadFromSearch={
            limit:-1,
            parentid:anId,
            uri:loadFromSearchURI,        
        };
        var onSuccess=function(data) {
            if (data === null) data = {};
            annotations = data.rows || [];
            var _i, _len;
            for (_i = 0, _len = annotations.length; _i < _len; _i++) {
                
                self._formatCatch(annotations[_i]);
            }
            replyElem.html(self.TEMPLATES.annotationReply({ 
                annotations: annotations
            }));
            var replyItems = $('.replies .replyItem');
            if (typeof replyItems !== 'undefined' && replyItems.length > 0) {
                annotations.forEach(function(ann) {
                    replyItems.each(function(item) {
                        var id = parseInt($(replyItems[item]).attr('annotationid'), 10);
                        if (id === ann.id) {
                            var perm = self.annotator.plugins.Permissions;
                            if (!perm.options.userAuthorize('delete', ann, perm.user)) {
                                $(replyItems[item]).find('.deleteReply').remove();
                            } else {
                                $(replyItems[item]).data('annotation', ann);
                            }
                        }
                    });
                });
            }
        };
        var id, options, request, url;
        var store = this.annotator.plugins.Store;
        id = loadFromSearch && loadFromSearch.id;
        url = store._urlFor(action, id);
        options = store._apiRequestOptions(action, loadFromSearch, onSuccess);
        request = $.ajax(url, options);
        request._id = id;
        request._action = action;
    },
    _onControlRepliesClick: function(evt) {
        var action = $(evt.target)[0].className;
        
        if (action === 'newReply') {
            var item = $(evt.target).parents('.annotationItem:first');
            var id = item.attr('annotationId');
            // Pre-show Adder
            this.annotator.adder.show();
            
            // Get elements
            var replyElem = $(evt.target).parents('.annotationItem:first').find('.annotationDetail');
            var adder =this.annotator.adder;
            var wrapper = $('.annotator-wrapper');

            // Calculate Editor position
            var positionLeft = videojs.findPosition($(evt.target).parent().find('.newReply')[0]);
            var positionAnnotator = videojs.findPosition(wrapper[0]);
            var positionAdder = {};

            positionAdder.left = positionLeft.left - positionAnnotator.left;
            positionAdder.top = positionLeft.top + 20 - positionAnnotator.top;

            adder.css(positionAdder);

            // Open a new annotator dialog
            this.annotator.onAdderClick();
            
            // Set vertical editor
            this.annotator.editor.resetOrientation();
            this.annotator.editor.invertY();
            this.annotator.editor.element.find('.annotator-widget').css('min-width', replyElem.css('width'));

            // set parent 
            var parentValue = $(this.annotator.editor.element).find(".reply-item span.parent-annotation");
            parentValue.html(id);
            var self = this;
            
        } else if (action === 'hideReplies') {
            var oldAction = $(evt.target).html();
            
            if (oldAction === 'Show Replies'){
                $(evt.target).html('Hide Replies');
            } else {
                $(evt.target).html('Show Replies');
                var replyElem = $(evt.target).parents('.annotationItem:first').find('.replies');
                replyElem.html('');
                return false;
            }
           
            // search
            this._refreshReplies(evt);
        } else if (action === 'deleteAnnotation') {
            if (confirm("Would you like to delete the annotation?")) {
                var annotator = this.annotator;
                var item = $(evt.target).parents('.annotationItem:first');
                var id = parseInt(item.attr('annotationId'), 10);
                var store = annotator.plugins.Store;
                var annotations = store.annotations;
                var permissions = annotator.plugins.Permissions;
                var annotation;
                annotations.forEach(function(ann) {
                   if (ann.id === id)
                       annotation = ann;
                });
                var authorized = permissions.options.userAuthorize('delete', annotation, permissions.user);
                if (authorized)
                    annotator.deleteAnnotation(annotation);
            }
        } else if (action === 'editAnnotation') {
           
            var annotator = this.annotator;
            var item = $(evt.target).parents('.annotationItem:first');
            var id = parseInt(item.attr('annotationId'), 10);
            var store = annotator.plugins.Store;
            var annotations = store.annotations;
            var permissions = annotator.plugins.Permissions;
            var annotation;
            annotations.forEach(function(ann) {
               if (ann.id === id)
                   annotation = ann;
            });
            var authorized = permissions.options.userAuthorize('update', annotation, permissions.user);
            if (authorized){
                // Get elements
                var wrapper = $('.annotator-wrapper');
                // Calculate Editor position
                var positionLeft = videojs.findPosition($(evt.target).parent().find('.editAnnotation')[0]);
                var positionAnnotator = videojs.findPosition(wrapper[0]);
                var positionAdder = {};

                positionAdder.left = positionLeft.left - positionAnnotator.left;
                positionAdder.top = positionLeft.top + 20 - positionAnnotator.top;
                var cleanup, offset, update;
                var _this = this.annotator;
                offset = positionAdder;
                update = function() {
                  cleanup();
                  return _this.updateAnnotation(annotation);
                };
                cleanup = function() {
                  _this.unsubscribe('annotationEditorHidden', cleanup);
                  return _this.unsubscribe('annotationEditorSubmit', update);
                };
                this.annotator.subscribe('annotationEditorHidden', cleanup);
                this.annotator.subscribe('annotationEditorSubmit', update);
                this.annotator.viewer.hide();
                this.annotator.showEditor(annotation, offset);                
            }
        }
    },
    _onShareControlsClick: function(evt) {
        var action = $(evt.target)[0].className;
        if (action === 'privacy_button') {
            
        } else if (action === 'groups_button') {
            alert("Coming soon...");
        } else if (action === 'reply_button') {
            var item = $(evt.target).parents('.annotationItem:first'),
                id = item.attr('annotationId');
            // New annotation
            var an = this.annotator.setupAnnotation(this.annotator.createAnnotation());
            an.text="010";
            an.parent = id;
        } else if (action === 'share_button') {

        }
    },
    _onPublicPrivateButtonClick: function(evt) {
        var action = $(evt.target).find('span');
        var userId = '';
    
        // Get userI
        switch (action.html()){
            case 'public':
                userId = '';
                break;
            case 'instructor':
                userId = this.options.instructor_email;
                break;
            default:
                userId = this.annotator.plugins.Permissions.user.id;
                break;
        }
        this.current_tab = action.html();
        
        // checks to make sure that Grouping is redone when switching tags in text annotations
        if (this.options.media === 'text') {
            if (typeof this.annotator.plugins.Grouping !== 'undefined') {
                // this is to check if user is is MyNotes instead of the annotation component
                this.annotator.plugins.Grouping.useGrouping = this.current_tab === 'public' ? 0 : 1;
            } 
            this.annotator.publish("changedTabsInCatch");
        }
        // Change userid and refresh
        this.changeUserId(userId);
    },
    _onSelectionButtonClick: function(evt) {
        var but = $(evt.target);
        var action = but.attr('media');
    
        // Get action
        if (action.length<=0) action="text"; // By default
        
        
        // Change media and refresh
        this.changeMedia(action);
    },
    _onMoreButtonClick: function(evt) {
        this.clean = false;
        var moreBut = this.element.find('.annotationListButtons .moreButtonCatch');
        var isLoading = moreBut.html() === 'More'?false:true;
        if(!isLoading)
            this.loadAnnotations();
    },
            
    _refresh:function(searchtype, searchInput) {
        var searchtype = searchtype || "";
        var searchInput = searchInput || ""; 
        this.clean = true;

        // the following cannot run in notes for there are no highlights
        if ($("#notesHolder").length === 0) {
            this._clearAnnotator();
        }
        
        var annotator = this.annotator;
        var loadFromSearch = annotator.plugins.Store.options.loadFromSearch;
        
        loadFromSearch.limit = this.options.pagination;
        loadFromSearch.offset = 0;
        loadFromSearch.media = this.options.media;
        loadFromSearch.userid = this.options.userId;
        
        loadFromSearch.username = "";
        loadFromSearch.tag = "";
        loadFromSearch.text = "";
        
        if (searchtype === "Users") {
            loadFromSearch.username = searchInput;
        } else if(searchtype === "Tags") {
            loadFromSearch.tag = searchInput;
        } else {
            loadFromSearch.text = searchInput;
        }
        annotator.plugins['Store'].loadAnnotationsFromSearch(loadFromSearch);
    },
    
    _onSearchButtonClick: function(evt) {
        var searchtype = this.element.find('.searchbox .dropdown-list').val();
        var searchInput = this.element.find('.searchbox input').val();
        this._refresh(searchtype, searchInput);
        
    },
    _onClearSearchButtonClick: function(evt) {
        this._refresh('', '');    
    },
    _clearAnnotator: function() {
        var annotator = this.annotator;
        var store = annotator.plugins.Store;
        var annotations = store.annotations.slice();
        
        annotations.forEach(function(ann){
            var child, h, _i, _len, _ref;
            if (ann.highlights !== undefined) {
                _ref = ann.highlights;
                for (_i = 0, _len = _ref.length; _i < _len; _i++) {
                    h = _ref[_i];
                    if (!(h.parentNode !== undefined)) {
                        continue;
                    }
                    child = h.childNodes[0];
                    $(h).replaceWith(h.childNodes);
                }
            }
            store.unregisterAnnotation(ann);
        });
    },
    _onDeleteReplyButtonClick : function(evt) {
        var annotator = this.annotator;
        var item = $(evt.target).parents('.replyItem:first');
        var id = item.attr('annotationid');
        var permissions = annotator.plugins.Permissions;
        var annotation = item.data('annotation');
        var authorized = permissions.options.userAuthorize('delete', annotation, permissions.user);
        if(authorized){
            if(confirm('Would you like to delete this reply?')){
                annotator.plugins['Store']._apiRequest('destroy', annotation, function(){});
                item.remove();
            }
        }
    },
    openLoadingGIF: function() {
        $('#mainCatch').append('<div class=\'annotations-loading-gif\'><img src="'+this.options.imageUrlRoot+'loading_bar.gif" /><br />Annotations Data Loading... Please Wait.</div>');
    },
}
