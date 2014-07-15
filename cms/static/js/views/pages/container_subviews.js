/**
 * Subviews (usually small side panels) for XBlockContainerPage.
 */
define(["jquery", "underscore", "gettext", "js/views/baseview", "js/views/utils/view_utils"],
    function ($, _, gettext, BaseView, ViewUtils) {

        var disabledCss = "is-disabled";

        /**
         * A view that calls render when "has_changes" or "published" values in XBlockInfo have changed
         * after a server sync operation.
         */
        var UnitStateListenerView =  BaseView.extend({

            // takes XBlockInfo as a model
            initialize: function() {
                this.model.on('sync', this.onSync, this);
            },

            onSync: function(model) {
                if (ViewUtils.hasChangedAttributes(model, ['has_changes', 'published'])) {
                   this.render();
                }
            },

            render: function() {}
        });

        /**
         * A controller for updating the "View Live" and "Preview" buttons.
         */
        var PreviewActionController = UnitStateListenerView.extend({

            render: function() {
                var previewAction = this.$el.find('.button-preview'),
                    viewLiveAction = this.$el.find('.button-view');
                if (this.model.get('published')) {
                    viewLiveAction.removeClass(disabledCss);
                }
                else {
                    viewLiveAction.addClass(disabledCss);
                }
                if (this.model.get('has_changes') || !this.model.get('published')) {
                    previewAction.removeClass(disabledCss);
                }
                else {
                    previewAction.addClass(disabledCss);
                }
            }
        });

        /**
         * Publisher is a view that supports the following:
         * 1) Publishing of a draft version of an xblock.
         * 2) Discarding of edits in a draft version.
         * 3) Display of who last edited the xblock, and when.
         * 4) Display of publish status (published, published with changes, changes with no published version).
         */
        var Publisher = BaseView.extend({
            events: {
                'click .action-publish': 'publish',
                'click .action-discard': 'discardChanges'
            },

            // takes XBlockInfo as a model

            initialize: function () {
                BaseView.prototype.initialize.call(this);
                this.template = this.loadTemplate('publish-xblock');
                this.model.on('sync', this.onSync, this);
                this.renderPage = this.options.renderPage;
            },

            onSync: function(model) {
                if (ViewUtils.hasChangedAttributes(model, ['has_changes', 'published', 'edited_on', 'edited_by'])) {
                   this.render();
                }
            },

            render: function () {
                this.$el.html(this.template({
                    has_changes: this.model.get('has_changes'),
                    published: this.model.get('published'),
                    edited_on: this.model.get('edited_on'),
                    edited_by: this.model.get('edited_by'),
                    published_on: this.model.get('published_on'),
                    published_by: this.model.get('published_by'),
                    released_to_students: this.model.get('released_to_students'),
                    release_date: this.model.get('release_date'),
                    release_date_from: this.model.get('release_date_from')
                }));

                return this;
            },

            publish: function (e) {
                var xblockInfo = this.model;
                if (e && e.preventDefault) {
                    e.preventDefault();
                }
                ViewUtils.runOperationShowingMessage(gettext('Publishing&hellip;'),
                    function () {
                        return xblockInfo.save({publish: 'make_public'}, {patch: true});
                    }).always(function() {
                        xblockInfo.set("publish", null);
                    }).done(function () {
                        xblockInfo.fetch();
                    });
            },

            discardChanges: function (e) {
                var xblockInfo = this.model, that=this, renderPage = this.renderPage;
                if (e && e.preventDefault) {
                    e.preventDefault();
                }
                ViewUtils.confirmThenRunOperation(gettext("Discard Changes"),
                    gettext("Are you sure you want to discard changes and revert to the last published version?"),
                    gettext("Discard Changes"),
                    function () {
                        ViewUtils.runOperationShowingMessage(gettext('Discarding Changes&hellip;'),
                            function () {
                                return xblockInfo.save({publish: 'discard_changes'}, {patch: true});
                            }).always(function() {
                                xblockInfo.set("publish", null);
                            }).done(function () {
                                renderPage();
                            });
                    }
                );
            }
        });


        /**
         * PublishHistory displays when and by whom the xblock was last published, if it ever was.
         */
        var PublishHistory = BaseView.extend({
            // takes XBlockInfo as a model

            initialize: function () {
                BaseView.prototype.initialize.call(this);
                this.template = this.loadTemplate('publish-history');
                this.model.on('sync', this.onSync, this);
            },

            onSync: function(model) {
                if (ViewUtils.hasChangedAttributes(model, ['published', 'published_on', 'published_by'])) {
                   this.render();
                }
            },

            render: function () {
                this.$el.html(this.template({
                    published: this.model.get('published'),
                    published_on: this.model.get('published_on'),
                    published_by: this.model.get('published_by')
                }));

                return this;
            }
        });

        return {
            'PreviewActionController': PreviewActionController,
            'Publisher': Publisher,
            'PublishHistory': PublishHistory
        };
    }); // end define();
