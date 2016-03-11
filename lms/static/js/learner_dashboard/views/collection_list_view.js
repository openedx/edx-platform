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
                    var childList = [];
                    this.collection.each(function(program){
                        var child = new this.childView({model:program});
                        childList.push(child.el);
                    }, this);
                    this.$el.html(childList);
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
