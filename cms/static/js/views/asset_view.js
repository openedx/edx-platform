CMS.Views.Asset = Backbone.View.extend({
    initialize: function() {
        this.template = _.template($("#asset-tpl").text());
        this.listenTo(this.model, "change", this.render);
    },

    tagName: "tr",

    events: {
        "click .remove-asset-button": "confirmDelete",
        "click .lock-asset-button": "lockAsset"
    },

    render: function() {
        this.$el.removeClass();

        this.$el.html(this.template({
            display_name: this.model.get('display_name'),
            thumbnail: this.model.get('thumbnail'),
            date_added: this.model.get('date_added'),
            url: this.model.get('url'),
            portable_url: this.model.get('portable_url'),
            locked: this.model.get('locked')}));

        // Add a class of "locked" to the tr element if appropriate.
        if (this.model.get('locked')) {
            this.$el.addClass('is-locked');
        }

        return this;
    },

    confirmDelete: function(e) {
        if(e && e.preventDefault) { e.preventDefault(); }
        var asset = this.model;
        new CMS.Views.Prompt.Warning({
            title: gettext("Delete File Confirmation"),
            message: gettext("Are you sure you wish to delete this item. It cannot be reversed!\n\nAlso any content that links/refers to this item will no longer work (e.g. broken images and/or links)"),
            actions: {
                primary: {
                    text: gettext("Delete"),
                    click: function (view) {
                        view.hide();
                        asset.destroy({
                                wait: true, // Don't remove the asset from the collection until successful.
                                success: function () {
                                    new CMS.Views.Notification.Confirmation({
                                        title: gettext("Your file has been deleted."),
                                        closeIcon: false,
                                        maxShown: 2000
                                    }).show()
                                }
                            }
                        );
                    }
                },
                secondary: [
                    {
                        text: gettext("Cancel"),
                        click: function (view) {
                            view.hide();
                        }
                    }
                ]
            }
        }).show();
    },

    lockAsset: function(e) {
        if(e && e.preventDefault) { e.preventDefault(); }
        var asset = this.model;
        var saving = new CMS.Views.Notification.Mini({
            title: gettext("Saving&hellip;")
        }).show();
        asset.save({'locked': !asset.get('locked')}, {
            wait: true, // This means we won't re-render until we get back the success state.
            success: function() {
                saving.hide();
            }
        });
    }
});
