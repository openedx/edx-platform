(function(define) {
    'use strict';

    define(['backbone',
        'jquery',
        'underscore',
        'gettext',
        'teams/js/views/team_utils',
        'text!teams/templates/team-profile-header-actions.underscore',
        'edx-ui-toolkit/js/utils/html-utils'],
        function(Backbone, $, _, gettext, TeamUtils, teamProfileHeaderActionsTemplate, HtmlUtils) {
            return Backbone.View.extend({

                errorMessage: gettext('An error occurred. Try again.'),
                alreadyTeamsetMemberMessage: gettext('You already belong to another team in this team set.'),
                teamFullMessage: gettext('This team is full.'),
                notJoinInstructorManagedTeam: gettext('Cannot join instructor managed team'),

                events: {
                    'click .action-primary': 'joinTeam',
                    'click .action-edit-team': 'editTeam'
                },

                initialize: function(options) {
                    this.teamEvents = options.teamEvents;
                    this.template = _.template(teamProfileHeaderActionsTemplate);
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
                    this.getUserTeamInfo(username, this.context.courseMaxTeamSize).done(function(info) {
                        teamHasSpace = info.teamHasSpace;

                        // if user is the member of current team then we wouldn't show anything
                        if (!info.memberOfCurrentTeam) {
                            if (info.alreadyInTeamset) {
                                showJoinButton = false;
                                message = info.memberOfCurrentTeam ? '' : view.alreadyTeamsetMemberMessage;
                            } else if (!teamHasSpace) {
                                showJoinButton = false;
                                message = view.teamFullMessage;
                            } else if (!info.isAdminOrStaff && info.isInstructorManagedTopic) {
                                showJoinButton = false;
                                message = view.notJoinInstructorManagedTeam;
                            } else {
                                showJoinButton = true;
                            }
                        }
                        HtmlUtils.setHtml(
                            view.$el,
                            HtmlUtils.template(teamProfileHeaderActionsTemplate)({
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
                        data: {username: view.context.userInfo.username, team_id: view.model.get('id')}
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

                getUserTeamInfo: function(username, courseMaxTeamSize) {
                    var deferred = $.Deferred();
                    var info = {
                        alreadyInTeamset: false,
                        memberOfCurrentTeam: false,
                        teamHasSpace: false,
                        isAdminOrStaff: false,
                        isInstructorManagedTopic: false
                    };

                    // this.topic.getMaxTeamSize() will return null for a managed team,
                    // but the size is considered to be arbitarily large.
                    var isInstructorManagedTopic = TeamUtils.isInstructorManagedTopic(this.topic.attributes.type);
                    var teamHasSpace = isInstructorManagedTopic ||
                        (this.model.get('membership').length < this.topic.getMaxTeamSize(courseMaxTeamSize));

                    info.memberOfCurrentTeam = TeamUtils.isUserMemberOfTeam(this.model.get('membership'), username);
                    info.isAdminOrStaff = this.context.userInfo.privileged || this.context.userInfo.staff;
                    info.isInstructorManagedTopic = isInstructorManagedTopic;

                    if (info.memberOfCurrentTeam) {
                        info.alreadyInTeamset = true;
                        info.memberOfCurrentTeam = true;
                        deferred.resolve(info);
                    } else {
                        if (teamHasSpace) {
                            var view = this; // eslint-disable-line vars-on-top
                            $.ajax({
                                type: 'GET',
                                url: view.context.teamMembershipsUrl,
                                data: {
                                    username: username,
                                    course_id: view.context.courseID,
                                    teamset_id: view.model.get('topic_id')
                                }
                            }).done(function(data) {
                                info.alreadyInTeamset = (data.count > 0);
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
