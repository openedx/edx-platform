/* JavaScript for reset option that can be done on a randomized LibraryContentBlock */
function LibraryContentReset(runtime, element) {
  $('.problem-reset-btn', element).click((e) => {
    e.preventDefault();
    $.post({
      url: runtime.handlerUrl(element, 'reset_selected_children'),
      success() {
        location.reload();
      },
    });
  });
}
