/* JavaScript for reset option that can be done on a randomized LibraryContentBlock */
function LibraryContentReset(runtime, element) {
  $('.problem-reset-btn', element).click((e) => {
    e.preventDefault();
    $.post({
      url: runtime.handlerUrl(element, 'reset_selected_children'),
      success(data) {
        edx.HtmlUtils.setHtml(element, edx.HtmlUtils.HTML(data));
        // Rebind the reset button for the block
        XBlock.initializeBlock(element);
        // Render the new set of problems (XBlocks)
        $(".xblock", element).each(function(i, child) {
          XBlock.initializeBlock(child);
        });
      },
    });
  });
}
