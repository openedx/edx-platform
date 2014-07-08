define(["backbone", "backbone.associations"], function(Backbone){
    var Topic = Backbone.AssociatedModel.extend({
        defaults: function(){
            return {
                name: "",
                description: "",
                order: this.collection ? this.collection.nextOrder(): 1
            };
        },
        isEmpty: function() {
            return !this.get('name') && !this.get('description');
        },
        parse: function(response) {
            if("title" in response && !("name" in response)) {
                response.name = response.title;
                delete response.title;
            }
            if("topic" in response && !("description" in response)) {
                response.description = response.topic;
                delete response.topic;
            }
            return response;
        },
        toJSON: function() {
            return {
                title: this.get('name'),
                description: this.get('description')
            };
        },

        validate: function(attrs, options) {
            if(!attrs.name && !attrs.description) {
                return {
                    message: "Topic name and description are both required",
                    attributes: {name: true, description: true}
                };
            } else if(!attrs.name) {
                return {
                    message: "Chapter name is required",
                    attributes: {name: true}
                };
            } else if (!attrs.description) {
                return {
                    message: "description is required",
                    attributes: {description: true}
                };
            }
        }
    });
    return Topic;
});