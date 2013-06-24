CMS.Models.Textbook = Backbone.AssociatedModel.extend({
    defaults: function() {
        return {
            name: "",
            chapters: new CMS.Collections.ChapterSet([{}]),
            showChapters: false
        };
    },
    relations: [{
        type: Backbone.Many,
        key: "chapters",
        relatedModel: "CMS.Models.EditChapter",
        collectionType: "CMS.Collections.ChapterSet"
    }],
    isEmpty: function() {
        return !this.get('name') && this.get('chapters').isEmpty();
    },
    parse: function(response) {
        var ret = $.extend(true, {}, response);
        if("tab_title" in ret && !("name" in ret)) {
            ret.name = ret.tab_title;
            delete ret.tab_title;
        }
        if("url" in ret && !("chapters" in ret)) {
            ret.chapters = {"url": ret.url};
            delete ret.url;
        }
        _.each(ret.chapters, function(chapter, i) {
            chapter.order = chapter.order || i+1;
        });
        return ret;
    },
    toJSON: function() {
        return {
            tab_title: this.get('name'),
            chapters: this.get('chapters').toJSON()
        };
    }
});
CMS.Collections.TextbookSet = Backbone.Collection.extend({
    model: CMS.Models.Textbook,
    url: function() { return CMS.URL.TEXTBOOK; },
    initialize: function() {
        this.listenTo(this, "editOne", this.editOne);
    },
    editOne: function(textbook) {
        this.editing = textbook;
    },
    save: function(options) {
        return this.sync('update', this, options);
    }
});
CMS.Models.Chapter = Backbone.AssociatedModel.extend({
    defaults: function() {
        return {
            name: "",
            asset_path: "",
            order: this.collection ? this.collection.nextOrder() : 1
        };
    },
    isEmpty: function() {
        return !this.get('name') && !this.get('asset_path');
    },
    parse: function(response) {
        if("title" in response && !("name" in response)) {
            response.name = response.title;
            delete response.title;
        }
        if("url" in response && !("asset_path" in response)) {
            response.asset_path = response.url;
            delete response.url;
        }
        return response;
    },
    toJSON: function() {
        return {
            title: this.get('name'),
            url: this.get('asset_path')
        };
    }
});
CMS.Collections.ChapterSet = Backbone.Collection.extend({
    model: CMS.Models.Chapter,
    comparator: "order",
    nextOrder: function() {
        if(!this.length) return 1;
        return this.last().get('order') + 1;
    },
    isEmpty: function() {
        return this.length === 0 || this.every(function(m) { return m.isEmpty(); });
    }
});
CMS.Models.FileUpload = Backbone.Model.extend({
    defaults: {
        "title": "",
        "message": "",
        "selectedFile": null,
        "uploading": false,
        "uploadedBytes": 0,
        "totalBytes": 0,
        "finished": false
    },
    validate: function(attrs, options) {
        if(attrs.selectedFile && attrs.selectedFile.type !== "application/pdf") {
            return gettext("Only PDF files can be uploaded. Please select a file ending in .pdf to upload.");
        }
    }
});
