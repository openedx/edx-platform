/* JavaScript for special editing operations that can be done on LibraryContentXBlock */
// This is a temporary UI improvements that will be removed when V2 content libraries became
// fully functional

/**
 * Toggle the "Problem Type" settings section depending on selected library type.
 * As for now, the V2 libraries don't support different problem types, so they can't be
 * filtered by it. We're hiding the Problem Type field for them.
 */
function checkProblemTypeShouldBeVisible(editor) {
    var libraries = editor.find('.wrapper-comp-settings.metadata_edit.is-active')
        .data().metadata.source_library_id.options;
    var selectedIndex = $("select[name='Library']", editor)[0].selectedIndex;
    var libraryKey = libraries[selectedIndex].value;
    var url = URI('/xblock')
        .segment(editor.find('.xblock.xblock-studio_view.xblock-studio_view-library_content.xblock-initialized')
        .data('usage-id'))
        .segment('handler')
        .segment('is_v2_library');

    $.ajax({
        type: 'POST',
        url: url,
        data: JSON.stringify({'library_key': libraryKey}),
        success: function(data) {
            var problemTypeSelect = editor.find("select[name='Problem Type']")
                .parents("li.field.comp-setting-entry.metadata_entry");
            data.is_v2 ? problemTypeSelect.hide() : problemTypeSelect.show();
        }
    });
}

var $librarySelect = $("select[name='Library']");

$(document).on('change', $librarySelect, (e) => {
    waitForEditorLoading();
})

$libraryContentEditors = $('.xblock-header.xblock-header-library_content');
$editBtns = $libraryContentEditors.find('.action-item.action-edit');
$(document).on('click', $editBtns, (e) => {
    console.log('edit clicked')
    waitForEditorLoading();
})

/**
 * Waits untill editor html loaded, than calls checks for Program Type field toggling.
 */
function waitForEditorLoading() {
    var checkContent = setInterval(function() {
        $modal = $('.xblock-editor');
        content = $modal.html();
        if (content) {
            clearInterval(checkContent);
            checkProblemTypeShouldBeVisible($modal);
        }
    }, 10);
}
// Initial call
waitForEditorLoading();
