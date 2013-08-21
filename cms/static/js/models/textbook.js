CMS.Models.Textbook = Backbone.AssociatedModel.extend({
    defaults: function() {
        return {
            name: "",
            chapters: new CMS.Collections.ChapterSet([{}]),
            showChapters: false,
            editing: false
        };
    },
    relations: [{
        type: Backbone.Many,
        key: "chapters",
        relatedModel: "CMS.Models.Chapter",
        collectionType: "CMS.Collections.ChapterSet"
    }],
    initialize: function() {
        this.setOriginalAttributes();
        return this;
    },
    setOriginalAttributes: function() {
        this._originalAttributes = this.parse(this.toJSON());
    },
    reset: function() {
        this.set(this._originalAttributes, {parse: true});
    },
    isDirty: function() {
        return !_.isEqual(this._originalAttributes, this.parse(this.toJSON()));
    },
    isEmpty: function() {
        return !this.get('name') && this.get('chapters').isEmpty();
    },
    url: function() {
        if(this.isNew()) {
            return CMS.URL.TEXTBOOKS + "/new";
        } else {
            return CMS.URL.TEXTBOOKS + "/" + this.id;
        }
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
    },
    // NOTE: validation functions should return non-internationalized error
    // messages. The messages will be passed through gettext in the template.
    validate: function(attrs, options) {
        if (!attrs.name) {
            return {
                message: "Textbook name is required",
                attributes: {name: true}
            };
        }
        if (attrs.chapters.length === 0) {
            return {
                message: "Please add at least one chapter",
                attributes: {chapters: true}
            };
        } else {
            // validate all chapters
            var invalidChapters = [];
            attrs.chapters.each(function(chapter) {
                if(!chapter.isValid()) {
                    invalidChapters.push(chapter);
                }
            });
            if(!_.isEmpty(invalidChapters)) {
                return {
                    message: "All chapters must have a name and asset",
                    attributes: {chapters: invalidChapters}
                };
            }
        }
    }
});
CMS.Collections.TextbookSet = Backbone.Collection.extend({
    model: CMS.Models.Textbook,
    url: function() { return CMS.URL.TEXTBOOKS; },
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
    },
    // NOTE: validation functions should return non-internationalized error
    // messages. The messages will be passed through gettext in the template.
    validate: function(attrs, options) {
        if(!attrs.name && !attrs.asset_path) {
            return {
                message: "Chapter name and asset_path are both required",
                attributes: {name: true, asset_path: true}
            };
        } else if(!attrs.name) {
            return {
                message: "Chapter name is required",
                attributes: {name: true}
            };
        } else if (!attrs.asset_path) {
            return {
                message: "asset_path is required",
                attributes: {asset_path: true}
            };
        }
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

