;(function (define) {
  'use strict';
  define(["backbone", "underscore", "text!teacher_dashboard/templates/loading_bar.underscore"], function(Backbone, _, LoadingBarTemplate) {
    var loadingBarTemplate = _.template(LoadingBarTemplate);

    var BaseView = Backbone.View.extend({
      constructor: function(options) {
        Backbone.View.prototype.constructor.apply(this, arguments);
        this.options = options;
        this.showLoadingBar();
      },

      render: function(context) {
        this.beforeRender();
        if (this.template) {
          context = _.extend({}, context, this.getContext());
          this.$el.html(this.template(context));
        }
        this.afterRender();
        return this;
      },

      getContext: function() {return {};},

      showLoadingBar: function() {
        this.$el.html(loadingBarTemplate({}));
      }
    });

    return BaseView;
  });
}).call(this, define || RequireJS.define);
