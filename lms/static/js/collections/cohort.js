(function(Backbone) {
    var CohortCollection = Backbone.Collection.extend({
        model : this.CohortModel,
        comparator: "name",

        parse: function(response) {
            return response.cohorts;
        }
    });
    this.CohortCollection = CohortCollection;
}).call(this, Backbone);
