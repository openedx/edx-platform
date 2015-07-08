;(function (define) {
    'use strict';

    define(['backbone',
            'underscore',
            'gettext',
            'js/components/header/views/header',
            'js/components/header/models/header',
            'js/components/tabbed/views/tabbed_view',
            'teams/js/views/topics',
            'teams/js/models/topic',
            'teams/js/collections/topic',
            'teams/js/views/teams',
            'teams/js/collections/team',
            'text!teams/templates/teams_tab.underscore'],
           function (Backbone, _, gettext, HeaderView, HeaderModel, TabbedView,
                     TopicsView, TopicModel, TopicCollection, TeamsView, TeamCollection, teamsTemplate) {
               var ViewWithHeader = Backbone.View.extend({
                   initialize: function (options) {
                       this.header = options.header;
                       this.main = options.main;
                   },

                   render: function () {
                       this.$el.html(_.template(teamsTemplate));
                       this.$('p.error').hide();
                       this.header.setElement(this.$('.teams-header')).render();
                       this.main.setElement(this.$('.page-content')).render();
                       return this;
                   }
               });

               var TeamTabView = Backbone.View.extend({
                   initialize: function(options) {
                       var TempTabView, router;
                       this.course_id = options.course_id;
                       this.topics = options.topics;
                       this.topic_url = options.topic_url;
                       this.teams_url = options.teams_url;
                       this.maxTeamSize = options.maxTeamSize;
                       // This slightly tedious approach is necessary
                       // to use regular expressions within Backbone
                       // routes, allowing us to capture which tab
                       // name is being routed to
                       router = this.router = new Backbone.Router();
                       _.each([
                           [':default', _.bind(this.routeNotFound, this)],
                           ['topics/:topic_id', _.bind(this.browseTopic, this)],
                           [new RegExp('^(browse)$'), _.bind(this.goToTab, this)],
                           [new RegExp('^(teams)$'), _.bind(this.goToTab, this)]
                       ], function (route) {
                           router.route.apply(router, route);
                       });
                       // TODO replace this with actual views!
                       TempTabView = Backbone.View.extend({
                           initialize: function (options) {
                               this.text = options.text;
                           },

                           render: function () {
                               this.$el.text(this.text);
                           }
                       });
                       this.topicsCollection = new TopicCollection(
                           this.topics,
                           {url: options.topics_url, course_id: this.course_id, parse: true}
                       ).bootstrap();
                       this.mainView = this.tabbedView = new ViewWithHeader({
                           header: new HeaderView({
                               model: new HeaderModel({
                                   description: gettext("See all teams in your course, organized by topic. Join a team to collaborate with other learners who are interested in the same topic as you are."),
                                   title: gettext("Teams")
                               })
                           }),
                           main: new TabbedView({
                               tabs: [{
                                   title: gettext('My Teams'),
                                   url: 'teams',
                                   view: new TempTabView({text: 'This is the new Teams tab.'})
                               }, {
                                   title: gettext('Browse'),
                                   url: 'browse',
                                   view: new TopicsView({
                                       collection: this.topicsCollection,
                                       router: this.router
                                   })
                               }],
                               router: this.router
                           })
                       });
                   },

                   render: function() {
                       this.mainView.setElement(this.$el).render();
                       this.hideWarning();
                       return this;
                   },

                   /**
                    * Render the list of teams for the given topic ID.
                    */
                   browseTopic: function (topicID) {
                       var self = this;
                       this.getTeamsView(topicID).done(function (teamsView) {
                           self.mainView = teamsView;
                           self.render();
                       });
                   },

                   /**
                    * Return a promise for the TeamsView for the given
                    * topic ID.
                    */
                   getTeamsView: function (topicID) {
                       // Lazily load the teams-for-topic view in
                       // order to avoid making an extra AJAX call.
                       if (!_.isUndefined(this.teamsView)
                               && this.teamsView.main.collection.topic_id === topicID) {
                           return this.identityPromise(this.teamsView);
                       }
                       var self = this,
                           teamCollection = new TeamCollection([], {
                               course_id: this.course_id,
                               url: this.teams_url,
                               topic_id: topicID,
                               per_page: 10
                           }),
                           teamPromise = teamCollection.goTo(1).fail(function (xhr) {
                               if (xhr.status === 400) {
                                   self.topicNotFound(topicID);
                               }
                           }),
                           topicPromise = this.getTopic(topicID).fail(function (xhr) {
                               if (xhr.status === 404) {
                                   self.topicNotFound(topicID);
                               }
                           });
                       return $.when(topicPromise, teamPromise).pipe(
                           _.bind(this.constructTeamView, this)
                       );
                   },

                   /**
                    * Given a topic and the results of the team
                    * collection's fetch(), return the team list view.
                    */
                   constructTeamView: function (topic, collectionResults) {
                       var self = this,
                           headerView = new HeaderView({
                               model: new HeaderModel({
                                   description: _.escape(topic.get('description')),
                                   title: _.escape(topic.get('name')),
                                   breadcrumbs: [{
                                       title: 'All topics',
                                       url: '#'
                                   }]
                               }),
                               events: {
                                   'click nav.breadcrumbs a.nav-item': function (event) {
                                       event.preventDefault();
                                       self.router.navigate('browse', {trigger: true});
                                   }
                               }
                           });
                       return new ViewWithHeader({
                           header: headerView,
                           main: new TeamsView({
                               collection: new TeamCollection(collectionResults[0], {
                                   course_id: this.course_id,
                                   url: this.teams_url,
                                   topic_id: topic.get('id'),
                                   per_page: 10,
                                   parse: true
                               }),
                               maxTeamSize: this.maxTeamSize
                           })
                       });
                   },

                   /**
                    * Get a topic given a topic ID.  Returns a jQuery deferred
                    * promise, since the topic may need to be fetched from the
                    * server.
                    * @param topicID the string identifier for the requested topic
                    * @returns a jQuery deferred promise for the topic.
                    */
                   getTopic: function (topicID) {
                       // Try finding topic in the current page of the
                       // topicCollection.  Otherwise call the topic endpoint.
                       var topic = this.topicsCollection.findWhere({'id': topicID}),
                           self = this;
                       if (topic) {
                           return this.identityPromise(topic);
                       } else {
                           var TopicModelWithUrl = TopicModel.extend({
                               url: function () { return self.topic_url.replace('topic_id', this.id); }
                           });
                           return (new TopicModelWithUrl({id: topicID })).fetch();
                       }
                   },

                   /**
                    * Immediately return a promise for the given
                    * object.
                    */
                   identityPromise: function (obj) {
                       return new $.Deferred().resolve(obj).promise();
                   },

                   /**
                    * Set up the tabbed view and switch tabs.
                    */
                   goToTab: function (tab) {
                       this.mainView = this.tabbedView;
                       // Note that `render` should be called first so
                       // that the tabbed view's element is set
                       // correctly.
                       this.render();
                       this.tabbedView.main.setActiveTab(tab);
                   },

                   // Error handling

                   routeNotFound: function (route) {
                       this.notFoundError(
                           interpolate(
                               gettext('The page "%(route)s" could not be found.'),
                               {route: route},
                               true
                           )
                       );
                   },

                   topicNotFound: function (topicID) {
                       this.notFoundError(
                           interpolate(
                               gettext('The topic "%(topic)s" could not be found.'),
                               {topic: topicID},
                               true
                           )
                       );
                   },

                   /**
                    * Called when the user attempts to navigate to a
                    * route that doesn't exist. "Redirects" back to
                    * the main teams tab, and adds an error message.
                    */
                   notFoundError: function (message) {
                       this.router.navigate('teams', {trigger: true});
                       this.showWarning(message);
                   },

                   showWarning: function (message) {
                       var warningEl = this.$('.warning');
                       warningEl.find('.copy').html('<p>' + message + '</p');
                       warningEl.toggleClass('is-hidden', false);
                   },

                   hideWarning: function () {
                       this.$('.warning').toggleClass('is-hidden', true);
                   }
               });

               return TeamTabView;
           });
}).call(this, define || RequireJS.define);
