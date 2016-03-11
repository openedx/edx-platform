;(function (define) {
    'use strict';

    define(['backbone'],
         function(
             Backbone
         ) {
            return Backbone.View.extend({
                initialize: function(data) {
                    this.childView = data.childView;
                },

                render: function() {
                    var cardList = [];
                    this.collection.each(function(program){
                        var cardView = new this.childView({model:program});
                        cardList.push(cardView.el);
                    }, this);
                    this.$el.html(cardList);
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
