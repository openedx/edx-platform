var CounterIconView = Backbone.View.extend({
  initialize: function(options){
      this.options = options;
      this.count_el = options.count_el;
      this.endpoints = options.endpoints;
      this.global_variables = options.global_variables;
      this.view_templates = options.view_templates;
      this.refresh_watcher = options.refresh_watcher;
      this.view_audios = options.view_audios;
      this.namespace = options.namespace;

      /* initialize the model using the API endpoint URL that was passed into us */
      this.model = new CounterIconModel();
      var model_url = this.endpoints.unread_notification_count;

      // apply namespacing - if set - to our Ajax calls
      if (this.namespace) {
          model_url = this.append_url_param(model_url, 'namespace', this.namespace);
      }

      this.model.url = model_url;

      /* get out main underscore view template */
      this.template = _.template($('#xns-counter-template').html());

      this.render();

      /* re-render if the model changes */
      this.listenTo(this.model,'change', this.modelChanged);

      /* make the async call to the backend REST API */
      /* after it loads, the listenTo event will file and */
      /* will call into the rendering */
      this.model.fetch();

      /* adding short-poll capabilities to refresh notification counter */
      if(this.refresh_watcher.name == 'short-poll'){
          var period = this.refresh_watcher.args.poll_period_secs;
          var self = this;
          setInterval(function() { self.autoRefreshNotifications(self); }, period * 1000);
      }
  },


  append_url_param: function(baseUrl, key, value) {
      key = encodeURI(key); value = encodeURIComponent(value);
      var path = baseUrl.split('?')[0];
      var kvp = baseUrl.split('?')[1].split('&');
      var i=kvp.length; var x; while(i--)
      {
          x = kvp[i].split('=');
          if (x[0]==key)
          {
              x[1] = value;
              kvp[i] = x.join('=');
              break;
          }
      }
      if(i<0) {kvp[kvp.length] = [key,value].join('=');}
      return path + '?' + kvp.join('&');
    },

  events: {
      'click': 'showPane'
  },

  /* cached notifications pane view */
  notification_pane: null,

  /* cached user_notifications_mark_true view */
  user_notifications_mark_true: null,

  template: null,

  modelChanged: function() {
      this.render();
  },

  refresh: function() {
    var self = this;
    this.model.fetch({
        success: function (resp) {
            self.render();
        }
       });
  },

  render: function () {
      var html = this.template(this.model.toJSON());
      this.count_el.html(html);

      // if we are display double digits the
      // styles might need to change, if so add a "multi-digit"
      // class

      // clear any set previous styles
      this.count_el.removeClass('multi-digit');
      this.count_el.removeClass('double-digit');

      if (this.model.has('count')) {
        var count = this.model.get('count');
        if(count > 99) {
          this.count_el.addClass('multi-digit');
        } else if (count > 9) {
          this.count_el.addClass('double-digit');
        }
      }
 },

 showPane: function(e) {
      if (!this.notification_pane) {

          this.notification_pane = new NotificationPaneView({
              counter_icon_view: this,
              el: this.options.pane_el,
              endpoints: this.options.endpoints,
              global_variables: this.global_variables,
              view_templates: this.view_templates,
              namespace: this.namespace
          });
          this.notification_pane.showPane();
          $('body').bind('click', this.hidePaneWhenClickedOutside);
      }
     else {
        if (this.notification_pane.isVisible()) {
          this.notification_pane.hidePane();
          $('body').unbind('click');
        }
        else {
          this.notification_pane.showPane();
          $('body').bind('click', this.hidePaneWhenClickedOutside);
        }
     }

     e.stopPropagation();
  },

 autoRefreshNotifications: function(counterView) {
     var currentModel = new CounterIconModel();
     currentModel.url = counterView.model.url;
     currentModel.fetch().done(function(){
         // if notification counter is incremented.
         if(currentModel.get('count') > counterView.model.get('count')){
             counterView.model = currentModel;

             // Is audio supported e.g. IE 9
             if (typeof window.Audio != 'undefined' && counterView.view_audios.notification_alert) {
                 var notification_alert = new Audio(counterView.view_audios.notification_alert);
                 notification_alert.play();
             }
             counterView.render();
             if (counterView.notification_pane) {

                 var url = null;

                 // if user is under the unread notification pane then fetch unread notifications.
                 if (counterView.notification_pane.selected_pane == "unread") {
                     url = counterView.options.endpoints.user_notifications_unread_only;
                 }
                 // if user is under the view-all notification pane then fetch all notifications.
                 else if (counterView.notification_pane.selected_pane == 'all') {
                     url = counterView.options.endpoints.user_notifications_all;
                 }

                 if(url !== null) {
                     counterView.notification_pane.collection.url = url;

                     // apply namespacing - if set
                     if (counterView.namespace) {
                         counterView.notification_pane.collection.url = counterView.notification_pane.append_url_param(
                             url, 'namespace', counterView.namespace);
                     }

                     counterView.notification_pane.hydrate();
                 }
             }
         }
     });
  },

 hidePaneWhenClickedOutside: function() {
   $(".xns-pane").hide();
   $('body').unbind('click');
 }
});
