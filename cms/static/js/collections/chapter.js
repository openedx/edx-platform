define(["backbone", "js/models/chapter"], function(Backbone, ChapterModel) {
    var ChapterCollection = Backbone.Collection.extend({
        model: ChapterModel,
        comparator: "order",
        nextOrder: function() {
            if(!this.length) return 1;
            return this.last().get('order') + 1;
        },
        isEmpty: function() {
            return this.length === 0 || this.every(function(m) { return m.isEmpty(); });
        }
    });
    return ChapterCollection;
});
