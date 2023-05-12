// eslint-disable-next-line no-undef
define(['jquery'], function($) {
    /**
     * Hides the modal and modal cover, using the standard selectors.
     * Note though that the class "is-fixed" on the modal cover
     * prevents the closing operation.
     */
    // eslint-disable-next-line no-var
    var hideModal = function(e) {
        if (e) {
            e.preventDefault();
        }

        /* eslint-disable-next-line no-use-before-define, no-var */
        var $modalCover = getModalCover();

        // Unit editors (module_edit) do not want the modal cover to hide when users click outside
        // of the editor. Users must press Cancel or Save to exit the editor.
        if (!$modalCover.hasClass('is-fixed')) {
            // eslint-disable-next-line no-use-before-define
            getModal().hide();
            // eslint-disable-next-line no-use-before-define
            hideModalCover($modalCover);
        }
    };

    /**
     * Hides just the modal cover. Caller can pass in a specific
     * element as the modal cover, otherwise the standard selector will be used.
     *
     * This method also unbinds the click handler on the modal cover.
     */
    // eslint-disable-next-line no-var
    var hideModalCover = function(modalCover) {
        // eslint-disable-next-line eqeqeq
        if (modalCover == undefined) {
            // eslint-disable-next-line no-use-before-define
            modalCover = getModalCover();
        }
        modalCover.hide();
        modalCover.removeClass('is-fixed');
        modalCover.unbind('click');
    };

    /**
     * Shows the modal and modal cover, using the standard selectors.
     */
    // eslint-disable-next-line no-var
    var showModal = function() {
        // eslint-disable-next-line no-use-before-define
        getModal().show();
        // eslint-disable-next-line no-use-before-define
        showModalCover();
    };

    /**
     * Shows just the modal cover. The caller can optionally choose
     * to have the class "is-fixed" added to the cover, and
     * the user can also choose to specify a custom click handler
     * for the modal cover.
     *
     * This method returns the modal cover element.
     */
    // eslint-disable-next-line no-var
    var showModalCover = function(addFixed, clickHandler) {
        /* eslint-disable-next-line no-use-before-define, no-var */
        var $modalCover = getModalCover();
        $modalCover.show();
        if (addFixed) {
            $modalCover.addClass('is-fixed');
        }
        $modalCover.unbind('click');
        if (clickHandler) {
            $modalCover.bind('click', clickHandler);
        } else {
            $modalCover.bind('click', hideModal);
        }
        return $modalCover;
    };

    // eslint-disable-next-line no-var
    var getModalCover = function() {
        return $('.modal-cover');
    };

    // eslint-disable-next-line no-var
    var getModal = function() {
        return $('.modal, .showAsModal');
    };

    return {
        showModal: showModal,
        hideModal: hideModal,
        showModalCover: showModalCover,
        hideModalCover: hideModalCover
    };
});
