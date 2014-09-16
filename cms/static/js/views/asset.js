define(["js/views/baseview", "underscore", "gettext", "js/views/feedback_prompt", "js/views/feedback_notification", "js/views/license-selector","js/utils/modal"],
    function(BaseView, _, gettext, PromptView, NotificationView, LicenseSelector, ModalUtils) {
var AssetView = BaseView.extend({
  initialize: function() {
    this.template = this.loadTemplate("asset");
    this.listenTo(this.model, "change:locked", this.updateLockState);
    this.licenseSelector = new LicenseSelector({model:this.model.get('license'), buttonSize: 'middle'});
  },
  tagName: "tr",
  events: {
    "click .remove-asset-button": "confirmDelete",
    "click .lock-checkbox": "lockAsset",
    "click .change-asset-license-button": "showLicenseModal",
  },

  render: function() {
    var uniqueId = _.uniqueId('lock_asset_');
    this.$el.html(this.template({
      display_name: this.model.get('display_name'),
      thumbnail: this.model.get('thumbnail'),
      date_added: this.model.get('date_added'),
      url: this.model.get('url'),
      license_editable: this.model.get('license_editable'),
      license_img: this.licenseSelector.img(),
      external_url: this.model.get('external_url'),
      portable_url: this.model.get('portable_url'),
      uniqueId: uniqueId
    }));
    this.licenseSelector.render();
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

  showLicenseModal: function(e) {
    ModalUtils.showModal(".change-license-modal");
    $(".change-license-modal .modal-body .license-selector").remove();
    $(".change-license-modal .modal-body").append(this.licenseSelector.render().$el);
    this.licenseSelector.delegateEvents();
    $(".change-license-modal .save-license-button").unbind().bind('click',$.proxy(this,'changeLicense'));

  },

  lockAsset: function(e) {
    var asset = this.model;
    var saving = new NotificationView.Mini({
      title: gettext("Saving&hellip;")
    }).show();
    asset.save({'locked': !asset.get('locked')}, {
      wait: true, // This means we won't re-render until we get back the success state.
      success: function() {
          saving.hide();
      }
    });
    },

  changeLicense: function() {
    if (this.licenseSelector.getLicense() == this.model.get('license')) {
      ModalUtils.hideModal(null,".change-license-modal");
      return;
    }

    var asset = this.model;
    var view = this;

    var saving = new NotificationView.Mini({
      title: gettext("Saving&hellip;")
    }).show();
    asset.save({'license': this.licenseSelector.getLicense()}, {
      wait: true, // This means we won't re-render until we get back the success state.
      success: function() {
          saving.hide();
          view.$el.find('.license-img').html(view.licenseSelector.img());
          ModalUtils.hideModal(null,".change-license-modal");
      }
    });
    }
});

return AssetView;
}); // end define()
