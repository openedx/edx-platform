define(["backbone", "js/models/topic"], function(Backbone, TopicModel) {
    var TopicCollection = Backbone.Collection.extend({
        model: TopicModel,
        comparator: "order",
        nextOrder: function() {
            if(!this.length) return 1;
            return this.last().get('order') + 1;
        },
        isEmpty: function() {
            return this.length === 0 || this.every(function(m) { return m.isEmpty(); });
        }
    });
    return TopicCollection;
});