/* globals DiscussionContentView, DiscussionUtil */
(function() {
    'use strict';
    var __hasProp = {}.hasOwnProperty,
        __extends = function(child, parent) {
            for (var key in parent) {
                if (__hasProp.call(parent, key)) {
                    child[key] = parent[key];
                }
            }
            function ctor() {
                this.constructor = child;
            }

            ctor.prototype = parent.prototype;
            child.prototype = new ctor();
            child.__super__ = parent.prototype;
            return child;
        };

    if (typeof Backbone !== "undefined" && Backbone !== null) {
        this.DiscussionContentView = (function(_super) {

            __extends(DiscussionContentView, _super);

            function DiscussionContentView() {
                var self = this;
                this.setWmdContent = function() {
                    return DiscussionContentView.prototype.setWmdContent.apply(self, arguments);
                };
                this.getWmdContent = function() {
                    return DiscussionContentView.prototype.getWmdContent.apply(self, arguments);
                };
                this.getWmdEditor = function() {
                    return DiscussionContentView.prototype.getWmdEditor.apply(self, arguments);
                };
                this.makeWmdEditor = function() {
                    return DiscussionContentView.prototype.makeWmdEditor.apply(self, arguments);
                };
                return DiscussionContentView.__super__.constructor.apply(this, arguments);
            }

            DiscussionContentView.prototype.events = {
                "click .discussion-flag-abuse": "toggleFlagAbuse",
                "keydown .discussion-flag-abuse": function(event) {
                    return DiscussionUtil.activateOnSpace(event, this.toggleFlagAbuse);
                }
            };

            DiscussionContentView.prototype.attrRenderer = {
                ability: function(ability) {
                    var action, selector, _ref, _results;
                    _ref = this.abilityRenderer;
                    _results = [];
                    for (action in _ref) {
                        if (_ref.hasOwnProperty(action)){
                            selector = _ref[action];
                            if (!ability[action]) {
                                _results.push(selector.disable.apply(this));
                            } else {
                                _results.push(selector.enable.apply(this));
                            }
                        }
                    }
                    return _results;
                }
            };

            DiscussionContentView.prototype.abilityRenderer = {
                editable: {
                    enable: function() {
                        return this.$(".action-edit").closest(".actions-item").removeClass("is-hidden");
                    },
                    disable: function() {
                        return this.$(".action-edit").closest(".actions-item").addClass("is-hidden");
                    }
                },
                can_delete: {
                    enable: function() {
                        return this.$(".action-delete").closest(".actions-item").removeClass("is-hidden");
                    },
                    disable: function() {
                        return this.$(".action-delete").closest(".actions-item").addClass("is-hidden");
                    }
                },
                can_openclose: {
                    enable: function() {
                        var self = this;
                        return _.each([".action-close", ".action-pin"], function(selector) {
                            return self.$(selector).closest(".actions-item").removeClass("is-hidden");
                        });
                    },
                    disable: function() {
                        var self = this;
                        return _.each([".action-close", ".action-pin"], function(selector) {
                            return self.$(selector).closest(".actions-item").addClass("is-hidden");
                        });
                    }
                },
                can_report: {
                    enable: function() {
                        return this.$(".action-report").closest(".actions-item").removeClass("is-hidden");
                    },
                    disable: function() {
                        return this.$(".action-report").closest(".actions-item").addClass("is-hidden");
                    }
                },
                can_vote: {
                    enable: function() {
                        return this.$(".action-vote").closest(".actions-item").removeClass("is-hidden");
                    },
                    disable: function() {
                        return this.$(".action-vote").closest(".actions-item").addClass("is-hidden");
                    }
                }
            };

            DiscussionContentView.prototype.renderPartialAttrs = function() {
                var attr, value, _ref, _results;
                _ref = this.model.changedAttributes();
                _results = [];
                for (attr in _ref) {
                    if (_ref.hasOwnProperty(attr)) {
                        value = _ref[attr];
                        if (this.attrRenderer[attr]) {
                            _results.push(this.attrRenderer[attr].apply(this, [value]));
                        } else {
                            _results.push(void 0);
                        }
                    }
                }
                return _results;
            };

            DiscussionContentView.prototype.renderAttrs = function() {
                var attr, value, _ref, _results;
                _ref = this.model.attributes;
                _results = [];
                for (attr in _ref) {
                    if (_ref.hasOwnProperty(attr)) {
                        value = _ref[attr];
                        if (this.attrRenderer[attr]) {
                            _results.push(this.attrRenderer[attr].apply(this, [value]));
                        } else {
                            _results.push(void 0);
                        }
                    }
                }
                return _results;
            };

            DiscussionContentView.prototype.makeWmdEditor = function(cls_identifier) {
                if (!this.$el.find(".wmd-panel").length) {
                    return DiscussionUtil.makeWmdEditor(this.$el, $.proxy(this.$, this), cls_identifier);
                }
            };

            DiscussionContentView.prototype.getWmdEditor = function(cls_identifier) {
                return DiscussionUtil.getWmdEditor(this.$el, $.proxy(this.$, this), cls_identifier);
            };

            DiscussionContentView.prototype.getWmdContent = function(cls_identifier) {
                return DiscussionUtil.getWmdContent(this.$el, $.proxy(this.$, this), cls_identifier);
            };

            DiscussionContentView.prototype.setWmdContent = function(cls_identifier, text) {
                return DiscussionUtil.setWmdContent(this.$el, $.proxy(this.$, this), cls_identifier, text);
            };

            DiscussionContentView.prototype.initialize = function() {
                var self = this;
                this.model.bind('change', this.renderPartialAttrs, this);
                return this.listenTo(this.model, "change:endorsed", function() {
                    if (self.model instanceof Comment) {
                        return self.trigger("comment:endorse");
                    }
                });
            };

            return DiscussionContentView;

        })(Backbone.View);
        this.DiscussionContentShowView = (function(_super) {
            __extends(DiscussionContentShowView, _super);

            function DiscussionContentShowView() {
                var self = this;
                this.toggleClose = function() {
                    return DiscussionContentShowView.prototype.toggleClose.apply(self, arguments);
                };
                this.toggleReport = function() {
                    return DiscussionContentShowView.prototype.toggleReport.apply(self, arguments);
                };
                this.togglePin = function() {
                    return DiscussionContentShowView.prototype.togglePin.apply(self, arguments);
                };
                this.toggleVote = function() {
                    return DiscussionContentShowView.prototype.toggleVote.apply(self, arguments);
                };
                this.toggleEndorse = function() {
                    return DiscussionContentShowView.prototype.toggleEndorse.apply(self, arguments);
                };
                this.toggleFollow = function() {
                    return DiscussionContentShowView.prototype.toggleFollow.apply(self, arguments);
                };
                this.handleSecondaryActionBlur = function() {
                    return DiscussionContentShowView.prototype.handleSecondaryActionBlur.apply(self, arguments);
                };
                this.handleSecondaryActionEscape = function() {
                    return DiscussionContentShowView.prototype.handleSecondaryActionEscape.apply(self, arguments);
                };
                this.toggleSecondaryActions = function() {
                    return DiscussionContentShowView.prototype.toggleSecondaryActions.apply(self, arguments);
                };
                this.updateButtonState = function() {
                    return DiscussionContentShowView.prototype.updateButtonState.apply(self, arguments);
                };
                return DiscussionContentShowView.__super__.constructor.apply(this, arguments);
            }

            DiscussionContentShowView.prototype.events = _.reduce(
                [
                    [".action-follow", "toggleFollow"],
                    [".action-answer", "toggleEndorse"],
                    [".action-endorse", "toggleEndorse"],
                    [".action-vote", "toggleVote"],
                    [".action-more", "toggleSecondaryActions"],
                    [".action-pin", "togglePin"],
                    [".action-edit", "edit"],
                    [".action-delete", "_delete"],
                    [".action-report", "toggleReport"],
                    [".action-close", "toggleClose"]
                ],
                function(obj, event) {
                    var funcName, selector;
                    selector = event[0];
                    funcName = event[1];
                    obj["click " + selector] = function(event) {
                        return this[funcName](event);
                    };
                    obj["keydown " + selector] = function(event) {
                        return DiscussionUtil.activateOnSpace(event, this[funcName]);
                    };
                    return obj;
                },
                {}
            );

            DiscussionContentShowView.prototype.updateButtonState = function(selector, checked) {
                var $button;
                $button = this.$(selector);
                $button.toggleClass("is-checked", checked);
                return $button.attr("aria-checked", checked);
            };

            DiscussionContentShowView.prototype.attrRenderer = $.extend(
                {},
                DiscussionContentView.prototype.attrRenderer,
                {
                    subscribed: function(subscribed) {
                        return this.updateButtonState(".action-follow", subscribed);
                    },
                    endorsed: function(endorsed) {
                        var $button, selector;
                        selector = this.model.get("thread").get("thread_type") === "question" ?
                            ".action-answer" :
                            ".action-endorse";
                        this.updateButtonState(selector, endorsed);
                        $button = this.$(selector);
                        $button.closest(".actions-item").toggleClass("is-hidden", !this.model.canBeEndorsed());
                        return $button.toggleClass("is-checked", endorsed);
                    },
                    votes: function(votes) {
                        var button, numVotes, selector, votesHtml, votesCountMsg;
                        selector = ".action-vote";
                        this.updateButtonState(selector, window.user.voted(this.model));
                        button = this.$el.find(selector);
                        numVotes = votes.up_count;
                        votesCountMsg = ngettext(
                            "there is currently %(numVotes)s vote", "there are currently %(numVotes)s votes", numVotes
                        );
                        button.find(".js-sr-vote-count").html(interpolate(votesCountMsg, {numVotes: numVotes }, true));
                        votesHtml = interpolate(ngettext("%(numVotes)s Vote", "%(numVotes)s Votes", numVotes), {
                            numVotes: numVotes
                        }, true);
                        button.find(".vote-count").html(votesHtml);
                        return this.$el.find('.display-vote .vote-count').html(votesHtml);
                    },
                    pinned: function(pinned) {
                        this.updateButtonState(".action-pin", pinned);
                        return this.$(".post-label-pinned").toggleClass("is-hidden", !pinned);
                    },
                    abuse_flaggers: function() {
                        var flagged;
                        flagged = this.model.isFlagged();
                        this.updateButtonState(".action-report", flagged);
                        return this.$(".post-label-reported").toggleClass("is-hidden", !flagged);
                    },
                    closed: function(closed) {
                        this.updateButtonState(".action-close", closed);
                        this.$(".post-label-closed").toggleClass("is-hidden", !closed);
                        return this.$(".display-vote").toggle(closed);
                    }
                }
            );

            DiscussionContentShowView.prototype.toggleSecondaryActions = function(event) {
                event.preventDefault();
                event.stopPropagation();
                this.secondaryActionsExpanded = !this.secondaryActionsExpanded;
                this.$(".action-more").toggleClass("is-expanded", this.secondaryActionsExpanded);
                this.$(".actions-dropdown")
                    .toggleClass("is-expanded", this.secondaryActionsExpanded)
                    .attr("aria-expanded", this.secondaryActionsExpanded);

                if (this.secondaryActionsExpanded) {
                    if (event.type === "keydown") {
                        this.$(".action-list-item:first").focus();
                    }
                    $("body").on("click", this.toggleSecondaryActions);
                    $("body").on("keydown", this.handleSecondaryActionEscape);
                    return this.$(".action-list-item").on("blur", this.handleSecondaryActionBlur);
                } else {
                    $("body").off("click", this.toggleSecondaryActions);
                    $("body").off("keydown", this.handleSecondaryActionEscape);
                    return this.$(".action-list-item").off("blur", this.handleSecondaryActionBlur);
                }
            };

            DiscussionContentShowView.prototype.handleSecondaryActionEscape = function(event) {
                if (event.keyCode === 27) {
                    this.toggleSecondaryActions(event);
                    return this.$(".action-more").focus();
                }
            };

            DiscussionContentShowView.prototype.handleSecondaryActionBlur = function(event) {
                var self = this;
                return setTimeout(function() {
                    if (self.secondaryActionsExpanded && self.$(".actions-dropdown :focus").length === 0) {
                        return self.toggleSecondaryActions(event);
                    }
                }, 10);
            };

            DiscussionContentShowView.prototype.toggleFollow = function(event) {
                var is_subscribing, msg, url;
                event.preventDefault();
                is_subscribing = !this.model.get("subscribed");
                url = this.model.urlFor(is_subscribing ? "follow" : "unfollow");
                if (is_subscribing) {
                    msg = gettext("We had some trouble subscribing you to this thread. Please try again.");
                } else {
                    msg = gettext("We had some trouble unsubscribing you from this thread. Please try again.");
                }
                return DiscussionUtil.updateWithUndo(this.model, {
                    "subscribed": is_subscribing
                }, {
                    url: url,
                    type: "POST",
                    $elem: $(event.currentTarget)
                }, msg);
            };

            DiscussionContentShowView.prototype.toggleEndorse = function(event) {
                var beforeFunc, is_endorsing, msg, updates, url,
                    self = this;
                event.preventDefault();
                is_endorsing = !this.model.get("endorsed");
                url = this.model.urlFor("endorse");
                updates = {
                    endorsed: is_endorsing,
                    endorsement: is_endorsing ? {
                        username: DiscussionUtil.getUser().get("username"),
                        user_id: DiscussionUtil.getUser().id,
                        time: new Date().toISOString()
                    } : null
                };
                if (this.model.get('thread').get('thread_type') === 'question') {
                    if (is_endorsing) {
                        msg = gettext("We had some trouble marking this response as an answer.  Please try again.");
                    } else {
                        msg = gettext("We had some trouble removing this response as an answer.  Please try again.");
                    }
                } else {
                    if (is_endorsing) {
                        msg = gettext("We had some trouble marking this response endorsed.  Please try again.");
                    } else {
                        msg = gettext("We had some trouble removing this endorsement.  Please try again.");
                    }
                }
                return DiscussionUtil.updateWithUndo(
                    this.model,
                    updates,
                    {
                        url: url,
                        type: "POST",
                        data: { endorsed: is_endorsing },
                        $elem: $(event.currentTarget)
                    },
                    msg,
                    function() { return self.trigger("comment:endorse"); }
                ).always(this.trigger("comment:endorse"));
            };

            DiscussionContentShowView.prototype.toggleVote = function(event) {
                var is_voting, updates, url, user,
                    self = this;
                event.preventDefault();
                user = DiscussionUtil.getUser();
                is_voting = !user.voted(this.model);
                url = this.model.urlFor(is_voting ? "upvote" : "unvote");
                updates = {
                    upvoted_ids: (is_voting ? _.union : _.difference)(user.get('upvoted_ids'), [this.model.id])
                };
                return DiscussionUtil.updateWithUndo(user, updates, {
                    url: url,
                    type: "POST",
                    $elem: $(event.currentTarget)
                }, gettext("We had some trouble saving your vote.  Please try again.")).done(function() {
                    if (is_voting) {
                        return self.model.vote();
                    } else {
                        return self.model.unvote();
                    }
                });
            };

            DiscussionContentShowView.prototype.togglePin = function(event) {
                var is_pinning, msg, url;
                event.preventDefault();
                is_pinning = !this.model.get("pinned");
                url = this.model.urlFor(is_pinning ? "pinThread" : "unPinThread");
                if (is_pinning) {
                    msg = gettext("We had some trouble pinning this thread. Please try again.");
                } else {
                    msg = gettext("We had some trouble unpinning this thread. Please try again.");
                }
                return DiscussionUtil.updateWithUndo(this.model, {
                    pinned: is_pinning
                }, {
                    url: url,
                    type: "POST",
                    $elem: $(event.currentTarget)
                }, msg);
            };

            DiscussionContentShowView.prototype.toggleReport = function(event) {
                var is_flagging, msg, updates, url;
                event.preventDefault();
                if (this.model.isFlagged()) {
                    is_flagging = false;
                    msg = gettext("We had some trouble removing your flag on this post.  Please try again.");
                } else {
                    is_flagging = true;
                    msg = gettext("We had some trouble reporting this post.  Please try again.");
                }
                url = this.model.urlFor(is_flagging ? "flagAbuse" : "unFlagAbuse");
                updates = {
                    abuse_flaggers: (is_flagging ? _.union : _.difference)(
                        this.model.get("abuse_flaggers"), [DiscussionUtil.getUser().id]
                    )
                };
                return DiscussionUtil.updateWithUndo(this.model, updates, {
                    url: url,
                    type: "POST",
                    $elem: $(event.currentTarget)
                }, msg);
            };

            DiscussionContentShowView.prototype.toggleClose = function(event) {
                var is_closing, msg, updates;
                event.preventDefault();
                is_closing = !this.model.get('closed');
                if (is_closing) {
                    msg = gettext("We had some trouble closing this thread.  Please try again.");
                } else {
                    msg = gettext("We had some trouble reopening this thread.  Please try again.");
                }
                updates = {
                    closed: is_closing
                };
                return DiscussionUtil.updateWithUndo(this.model, updates, {
                    url: this.model.urlFor("close"),
                    type: "POST",
                    data: updates,
                    $elem: $(event.currentTarget)
                }, msg);
            };

            DiscussionContentShowView.prototype.getAuthorDisplay = function() {
                return _.template($("#post-user-display-template").html())({
                    username: this.model.get('username') || null,
                    user_url: this.model.get('user_url'),
                    is_community_ta: this.model.get('community_ta_authored'),
                    is_staff: this.model.get('staff_authored')
                });
            };

            DiscussionContentShowView.prototype.getEndorserDisplay = function() {
                var endorsement;
                endorsement = this.model.get('endorsement');
                if (endorsement && endorsement.username) {
                    return _.template($("#post-user-display-template").html())({
                        username: endorsement.username,
                        user_url: DiscussionUtil.urlFor('user_profile', endorsement.user_id),
                        is_community_ta: DiscussionUtil.isTA(endorsement.user_id),
                        is_staff: DiscussionUtil.isStaff(endorsement.user_id)
                    });
                } else {
                    return null;
                }
            };

            return DiscussionContentShowView;

        }).call(this, this.DiscussionContentView);
    }

}).call(window);
