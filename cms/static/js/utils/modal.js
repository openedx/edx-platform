define(['jquery'], function($) {
    /**
     * Hides the modal and modal cover, using the standard selectors.
     * Note though that the class "is-fixed" on the modal cover
     * prevents the closing operation.
     */
    var hideModal = function(e) {
        if (e) {
            e.preventDefault();
        }

        var $modalCover = getModalCover();

        // Unit editors (module_edit) do not want the modal cover to hide when users click outside
        // of the editor. Users must press Cancel or Save to exit the editor.
        if (!$modalCover.hasClass('is-fixed')) {
            getModal().hide();
            hideModalCover($modalCover);
        }
    };

    /**
     * Hides just the modal cover. Caller can pass in a specific
     * element as the modal cover, otherwise the standard selector will be used.
     *
     * This method also unbinds the click handler on the modal cover.
     */
    var hideModalCover = function(modalCover) {
        if (modalCover == undefined) {
            modalCover = getModalCover();
        }
        modalCover.hide();
        modalCover.removeClass('is-fixed');
        modalCover.unbind('click');
    };

    /**
     * Shows the modal and modal cover, using the standard selectors.
     */
    var showModal = function() {
        getModal().show();
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
    var showModalCover = function(addFixed, clickHandler) {
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

    var getModalCover = function() {
        return $('.modal-cover');
    };

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
