CMS.Views.Asset = Backbone.View.extend({
    initialize: function() {
        this.template = _.template($("#asset-tpl").text());
    },

    tagName: "tr",

    events: {
        "click .remove-asset-button": "confirmDelete"
    },

    render: function() {
        this.$el.html(this.template({
            display_name: this.model.get('display_name'),
            thumbnail: this.model.get('thumbnail'),
            date_added: this.model.get('date_added'),
            url: this.model.get('url'),
            portable_url: this.model.get('portable_url')}));
        return this;
    },

    confirmDelete: function(e) {
        if(e && e.preventDefault) { e.preventDefault(); }
        var asset = this.model, collection = this.model.collection;
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
    }
});
