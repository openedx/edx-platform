define(["js/views/baseview", "underscore", "gettext", "common/js/components/views/feedback_prompt",
      "common/js/components/views/feedback_notification"],
    function(BaseView, _, gettext, PromptView, NotificationView) {
var AssetView = BaseView.extend({
  initialize: function() {
    this.template = this.loadTemplate("asset");
    this.listenTo(this.model, "change:locked", this.updateLockState);
  },
  tagName: "tr",
  events: {
    "click .remove-asset-button": "confirmDelete",
    "click .lock-checkbox": "lockAsset"
  },

  render: function() {
    var uniqueId = _.uniqueId('lock_asset_');
    this.$el.html(this.template({
      display_name: this.model.get('display_name'),
      thumbnail: this.model.get('thumbnail'),
      date_added: this.model.get('date_added'),
      url: this.model.get('url'),
      external_url: this.model.get('external_url'),
      portable_url: this.model.get('portable_url'),
      asset_type: this.model.get_extension(),
      uniqueId: uniqueId
    }));
    this.updateLockState();
    return this;
  },

  updateLockState: function () {
    var locked_class = "is-locked";

    // Add a class of "locked" to the tr element if appropriate,
    // and toggle locked state of hidden checkbox.
    if (this.model.get('locked')) {
      this.$el.addClass(locked_class);
      this.$el.find('.lock-checkbox').attr('checked','checked');
    }
    else {
      this.$el.removeClass(locked_class);
      this.$el.find('.lock-checkbox').removeAttr('checked');
    }
  },

  confirmDelete: function(e) {
    if(e && e.preventDefault) { e.preventDefault(); }
    var asset = this.model, collection = this.model.collection;
    new PromptView.Warning({
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
                  new NotificationView.Confirmation({
                    title: gettext("Your file has been deleted."),
                    closeIcon: false,
                    maxShown: 2000
                  }).show();
                }
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
  },

  lockAsset: function(e) {
    var asset = this.model;
    var saving = new NotificationView.Mini({
      title: gettext("Saving")
    }).show();
    asset.save({'locked': !asset.get('locked')}, {
      wait: true, // This means we won't re-render until we get back the success state.
      success: function() {
          saving.hide();
      }
    });
    }
});

return AssetView;
}); // end define()
