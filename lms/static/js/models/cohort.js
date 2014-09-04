(function(Backbone) {
    var CohortModel = Backbone.Model.extend({
        idAttribute: 'id',
        defaults: {
            name: '',
            user_count: 0
        }
    });

    this.CohortModel = CohortModel;
}).call(this, Backbone);
