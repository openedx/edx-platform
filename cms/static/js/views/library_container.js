define(["jquery", "underscore", "js/views/paged_container", "js/utils/module", "gettext", "js/views/feedback_notification",
        "js/views/paging_header", "js/views/paging_footer"],
    function ($, _, PagedContainerView) {
        // To be extended with Library-specific features later.
        var LibraryContainerView = PagedContainerView;
        return LibraryContainerView;
    }); // end define();
