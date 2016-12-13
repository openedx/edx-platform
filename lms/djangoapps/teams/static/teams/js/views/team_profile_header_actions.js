(function(define) {
    'use strict';

    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'edx-ui-toolkit/js/utils/html-utils',
            'teams/js/views/team_utils',
            'text!teams/templates/team-profile-header-actions.underscore'],
        function(Backbone, $, _, gettext, HtmlUtils, TeamUtils, teamProfileHeaderActionsTemplate) {
            return Backbone.View.extend({

                errorMessage: gettext('An error occurred. Try again.'),
                alreadyMemberMessage: gettext('You already belong to another team.'),
                teamFullMessage: gettext('This team is full.'),

                events: {
                    'click .action-primary': 'joinTeam',
                    'click .action-edit-team': 'editTeam'
                },

                initialize: function(options) {
                    this.teamEvents = options.teamEvents;
                    this.template = HtmlUtils.template(teamProfileHeaderActionsTemplate);
                    this.context = options.context;
                    this.showEditButton = options.showEditButton;
                    this.topic = options.topic;
                    this.listenTo(this.model, 'change', this.render);
                },

                render: function() {
                    var view = this,
                        username = this.context.userInfo.username,
                        message,
                        showJoinButton,
                        teamHasSpace;
                    this.getUserTeamInfo(username, this.context.maxTeamSize).done(function(info) {
                        teamHasSpace = info.teamHasSpace;

                        // if user is the member of current team then we wouldn't show anything
                        if (!info.memberOfCurrentTeam) {
                            showJoinButton = !info.alreadyMember && teamHasSpace;

                            if (info.alreadyMember) {
                                message = info.memberOfCurrentTeam ? '' : view.alreadyMemberMessage;
                            } else if (!teamHasSpace) {
                                message = view.teamFullMessage;
                            }
                        }

                        HtmlUtils.setHtml(
                            view.$el,
                            view.template({
                                showJoinButton: showJoinButton,
                                message: message,
                                showEditButton: view.showEditButton
                            })
                        );
                    });
                    return view;
                },

                joinTeam: function(event) {
                    var view = this;

                    event.preventDefault();
                    $.ajax({
                        type: 'POST',
                        url: view.context.teamMembershipsUrl,
                        data: {'username': view.context.userInfo.username, 'team_id': view.model.get('id')}
                    }).done(function() {
                        view.model.fetch()
                            .done(function() {
                                view.teamEvents.trigger('teams:update', {
                                    action: 'join',
                                    team: view.model
                                });
                            });
                    }).fail(function(data) {
                        TeamUtils.parseAndShowMessage(data, view.errorMessage);
                    });
                },

                getUserTeamInfo: function(username, maxTeamSize) {
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
                                url: view.context.teamMembershipsUrl,
                                data: {'username': username, 'course_id': view.context.courseID}
                            }).done(function(data) {
                                info.alreadyMember = (data.count > 0);
                                info.memberOfCurrentTeam = false;
                                info.teamHasSpace = teamHasSpace;
                                deferred.resolve(info);
                            }).fail(function(data) {
                                TeamUtils.parseAndShowMessage(data, view.errorMessage);
                                deferred.reject();
                            });
                        } else {
                            deferred.resolve(info);
                        }
                    }

                    return deferred.promise();
                },

                editTeam: function(event) {
                    event.preventDefault();
                    Backbone.history.navigate(
                        'teams/' + this.topic.id + '/' + this.model.get('id') + '/edit-team',
                        {trigger: true}
                    );
                }
            });
        });
}).call(this, define || RequireJS.define);
