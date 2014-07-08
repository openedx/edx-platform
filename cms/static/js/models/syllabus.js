define(["backbone", "underscore", "js/models/topic", "js/collections/topic",
        "backbone.associations","coffee/src/main"],
    function(Backbone, _, TopicModel, TopicCollection) {

    var Syllabus = Backbone.AssociatedModel.extend({
        defaults: function() {
            return {
                name: "",
                topics: new TopicCollection([{}]),
                showTopics: false,
                editing: false
            };
        },
        relations: [{
            type: Backbone.Many,
            key: "topics",
            relatedModel: TopicModel,
            collectionType: TopicCollection
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
            return !this.get('name') && this.get('topics').isEmpty();
        },
        urlRoot: function() { return CMS.URL.SYLLABUSES; },
        parse: function(response) {
            var ret = $.extend(true, {}, response);
            if("tab_title" in ret && !("name" in ret)) {
                ret.name = ret.tab_title;
                delete ret.tab_title;
            }
            if("url" in ret && !("topics" in ret)) {
                ret.topics = {"url": ret.url};
                delete ret.url;
            }
            _.each(ret.topics, function(topic, i) {
                topic.order = topic.order || i+1;
            });
            return ret;
        },
        toJSON: function() {
            return {
                tab_title: this.get('name'),
                topics: this.get('topics').toJSON()
            };
        },
        // NOTE: validation functions should return non-internationalized error
        // messages. The messages will be passed through gettext in the template.
        validate: function(attrs, options) {
            if (!attrs.name) {
                return {
                    message: "Secction name is required",
                    attributes: {name: true}
                };
            }
            if (attrs.topics.length === 0) {
                return {
                    message: "Please add at least one topic",
                    attributes: {topics: true}
                };
            } else {
                // validate all chapters
                var invalidTopics= [];
                attrs.topics.each(function(topic) {
                    if(!topic.isValid()) {
                        invalidTopics.push(topic);
                    }
                });
                if(!_.isEmpty(invalidTopics)) {
                    return {
                        message: "All topic must have a name and description",
                        attributes: {topics: invalidTopics}
                    };
                }
            }
        }
    });
    return Syllabus;
});
