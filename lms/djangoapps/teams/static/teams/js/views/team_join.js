;(function (define) {
'use strict';

define(['backbone',
        'underscore',
        'gettext',
        'teams/js/views/team_utils',
        'text!teams/templates/team-join.underscore'],
       function (Backbone, _, gettext, TeamUtils, teamJoinTemplate) {
           return Backbone.View.extend({

               errorMessage: gettext("An error occurred. Try again."),
               alreadyMemberMessage: gettext("You already belong to another team."),
               teamFullMessage: gettext("This team is full."),

               events: {
                   "click .action-primary": "joinTeam"
               },

               initialize: function(options) {
                   this.template = _.template(teamJoinTemplate);
                   this.maxTeamSize = options.maxTeamSize;
                   this.currentUsername = options.currentUsername;
                   this.teamMembershipsUrl = options.teamMembershipsUrl;
                   _.bindAll(this, 'render', 'joinTeam', 'getUserTeamInfo');
                   this.listenTo(this.model, "change", this.render);
               },

               render: function() {
                   var message,
                       showButton,
                       teamHasSpace;

                   var view = this;
                   this.getUserTeamInfo(this.currentUsername, view.maxTeamSize).done(function (info) {
                       teamHasSpace = info.teamHasSpace;

                       // if user is the member of current team then we wouldn't show anything
                       if (!info.memberOfCurrentTeam) {
                           showButton = !info.alreadyMember && teamHasSpace;

                           if (info.alreadyMember) {
                               message = info.memberOfCurrentTeam ? '' : view.alreadyMemberMessage;
                           } else if (!teamHasSpace) {
                               message = view.teamFullMessage;
                           }
                       }

                       view.$el.html(view.template({showButton: showButton, message: message}));
                   });
                   return view;
               },

               joinTeam: function () {
                   var view = this;
                   $.ajax({
                       type: 'POST',
                       url: view.teamMembershipsUrl,
                       data: {'username': view.currentUsername, 'team_id': view.model.get('id')}
                   }).done(function (data) {
                       view.model.fetch({});
                   }).fail(function (data) {
                       TeamUtils.parseAndShowMessage(data, view.errorMessage);
                   });
               },

               getUserTeamInfo: function (username, maxTeamSize) {
                   var deferred = $.Deferred();
                   var info = {
                       alreadyMember: false,
                       memberOfCurrentTeam: false,
                       teamHasSpace: false
                   };

                   info.memberOfCurrentTeam = TeamUtils.isUserMemberOfTeam(this.model.get('membership'), username);
                   var teamHasSpace = this.model.get('membership').length < maxTeamSize;

                   if (info.memberOfCurrentTeam) {
                       info.alreadyMember = true;
                       info.memberOfCurrentTeam = true;
                       deferred.resolve(info);
                   } else {
                       if (teamHasSpace) {
                           var view = this;
                           $.ajax({
                               type: 'GET',
                               url: view.teamMembershipsUrl,
                               data: {'username': username}
                           }).done(function (data) {
                               info.alreadyMember = (data.count > 0);
                               info.memberOfCurrentTeam = false;
                               info.teamHasSpace = teamHasSpace;
                               deferred.resolve(info);
                           }).fail(function (data) {
                               TeamUtils.parseAndShowMessage(data, view.errorMessage);
                               deferred.reject();
                           });
                       } else {
                           deferred.resolve(info);
                       }
                   }

                   return deferred.promise();
               }
           });
       });
}).call(this, define || RequireJS.define);
