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
            if("description" in response && !("description" in response)) {
                response.description = response.description;
                delete response.description;
            }
            return response;
        },
        toJSON: function() {
            return {
                title: this.get('name'),
                description: this.get('description')
            };
        },
    });
    return Topic;
});