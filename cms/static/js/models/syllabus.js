define(["backbone", "underscore", "js/models/topic", "js/collections/topic", "backbone.associations"],
    function(Backbone, _, TopicModel, TopicCollection) {

    var Syllabus = Backbone.AssociatedModel.extend({
        defaults: function() {
            return {
                name: "",
                sections: new TopicCollection([{}]),
                showTopcis: false,
                editing: false
            };
        },
        relations: [{
            type: Backbone.Many,
            key: "sections",
            relatedModel: TopicModel,
            collectionType: TopicCollection
        }],
        initialize: function() {
            this.setOriginalAttributes();
            return this
|        },
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
            return !this.get('name') && this.get('sections').isEmpty();
        },
        url: function() {
            if(this.isNew()) {
                return CMS.URL.SYLLABUS + "/new";
            } else {
                return CMS.URL.SYLLABUS + "/" + this.id;
            }
        },
        parse: function(response) {
            var ret = $.extend(true, {}, response);
            if("tab_title" in ret && !("name" in ret)) {
                ret.name = ret.tab_title;
                delete ret.tab_title;
            }
            if("url" in ret && !("sections" in ret)) {
                ret.sections = {"url": ret.url};
                delete ret.url;
            }
            _.each(ret.sections, function(section, i) {
                section.order = section.order || i+1;
            });
            return ret;
        },
        toJSON: function() {
            return {
                tab_title: this.get('name'),
                sections: this.get('sections').toJSON()
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
            if (attrs.sections.length === 0) {
                return {
                    message: "Please add at least one topic",
                    attributes: {sections: true}
                };
            } else {
                // validate all chapters
                var invalidSections = [];
                attrs.sections.each(function(section) {
                    if(!section.isValid()) {
                        invalidSections.push(section);
                    }
                });
                if(!_.isEmpty(invalidSections)) {
                    return {
                        message: "All topic must have a name and description",
                        attributes: {sections: invalidSections}
                    };
                }
            }
        }
    });
    return Syllabus;
});
