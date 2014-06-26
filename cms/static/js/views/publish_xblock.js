/**
 * XBlockPublisher is a view that supports the following:
 * 1) Publishing of a draft version of an xblock.
 * 2) Discarding of edits in a draft version.
 * 3) Display of who last edited the xblock, and when.
 * 4) Display of publish status (published, published with changes, changes with no published version).
 */
define(["jquery", "underscore", "gettext", "js/views/baseview", "js/views/feedback_prompt"],
    function ($, _, gettext, BaseView, PromptView) {
        'use strict';
        var XBlockPublisher = BaseView.extend({
            events: {
                'click .publish-button': 'publish',
                'click .discard-changes-button': 'discardChanges'
            },

            // takes XBlockInfo as a model

            initialize: function () {
                BaseView.prototype.initialize.call(this);
                this.template = this.loadTemplate('publish-xblock');
                this.model.on('sync', this.onSync, this);
            },

            onSync: function(e) {
                if (('has_changes' in e.changedAttributes()) || ('published' in e.changedAttributes()) ||
                    ('edited_on' in e.changedAttributes()) || ('edited_by' in e.changedAttributes())) {
                   this.render();
                }
            },

            render: function () {
                console.log("render!");
                this.$el.html(this.template({
                    has_changes: this.model.get('has_changes'),
                    published: this.model.get('published'),
                    edited_on: this.model.get('edited_on'),
                    edited_by: this.model.get('edited_by')
                }));

                return this;
            },

            publish: function (e) {
                var xblockInfo = this.model;
                if (e && e.preventDefault) {
                    e.preventDefault();
                }
                this.runOperationShowingMessage(gettext('Publishing&hellip;'),
                    function () {
                        return xblockInfo.save({publish: 'make_public'});
                    }).done(function () {
                        xblockInfo.fetch();
                    });
            },

            discardChanges: function (e) {
                if (e && e.preventDefault) {
                    e.preventDefault();
                }
                var xblockInfo = this.model,
                    view;
                view = new PromptView.Warning({
                    title: gettext("Discard Changes"),
                    message: gettext("Are you sure you want to discard changes and revert to the last published version?"),
                    actions: {
                        primary: {
                            text: gettext("Discard Changes"),
                            click: function (view) {
                                view.hide();
                                $.ajax({
                                    type: 'DELETE',
                                    url: xblockInfo.url() + "?" + $.param({
                                        recurse: true
                                    })
                                }).success(function () {
                                    return window.location.reload();
                                });
                            }
                        },
                        secondary: {
                            text: gettext("Cancel"),
                            click: function (view) {
                                view.hide();
                            }
                        }
                    }
                }).show();
            }
        });

        return XBlockPublisher;
    }); // end define();