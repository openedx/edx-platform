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


(function(Backbone) {
    var CohortMessageModel = Backbone.Model.extend({
        defaults: {
            added: [],
            changed: [],
            present: [],
            unknown: []
        }
    });

    this.CohortMessageModel = CohortMessageModel;
}).call(this, Backbone);
