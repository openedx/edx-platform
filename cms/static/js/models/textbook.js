define(['backbone', 'underscore', 'gettext', 'js/models/chapter', 'js/collections/chapter',
        'backbone.associations', 'cms/js/main'],
    function(Backbone, _, gettext, ChapterModel, ChapterCollection) {
        var Textbook = Backbone.AssociatedModel.extend({
            defaults: function() {
                return {
                    name: '',
                    chapters: new ChapterCollection([{}]),
                    showChapters: false,
                    editing: false
                };
            },
            relations: [{
                type: Backbone.Many,
                key: 'chapters',
                relatedModel: ChapterModel,
                collectionType: ChapterCollection
            }],
            initialize: function() {
                this.setOriginalAttributes();
                return this;
            },
            customSave: function(options) {
                var model = this;
                if (!model.id) {
                    var method = 'POST';
                    var url = model.urlRoot();
                } else {
                    var method = 'PUT';
                    var url = model.urlRoot()+'/'+model.id;
                }
                $.ajax({
                    url: url,
                    type: method,
                    dataType: 'json',
                    data: JSON.stringify(model.toJSON()),
                    success: function(object, status) {
                        if (options.success) options.success(model, object, method);
                        if (options.complete) options.complete(model, object, method);
                    },
                    error: function(xhr, status, error) {
                        if (options.error) options.error(model, object.content);
                    }
                });
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
            urlRoot: function() { return CMS.URL.TEXTBOOKS; },
            parse: function(response) {
                var ret = $.extend(true, {}, response);
                if ('tab_title' in ret && !('name' in ret)) {
                    ret.name = ret.tab_title;
                    delete ret.tab_title;
                }
                if ('url' in ret && !('chapters' in ret)) {
                    ret.chapters = {'url': ret.url};
                    delete ret.url;
                }
                _.each(ret.chapters, function(chapter, i) {
                    chapter.order = chapter.order || i + 1;
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
                        message: gettext('Textbook name is required'),
                        attributes: {name: true}
                    };
                }
                if (attrs.chapters.length === 0) {
                    return {
                        message: gettext('Please add at least one chapter'),
                        attributes: {chapters: true}
                    };
                } else {
                // validate all chapters
                    var invalidChapters = [];
                    attrs.chapters.each(function(chapter) {
                        if (!chapter.isValid()) {
                            invalidChapters.push(chapter);
                        }
                    });
                    if (!_.isEmpty(invalidChapters)) {
                        return {
                            message: gettext('All chapters must have a name and asset'),
                            attributes: {chapters: invalidChapters}
                        };
                    }
                }
            }
        });
        return Textbook;
    });
