$(document).ready(function () {
    $('#cheatsheetLink').click(function() {
        $('#cheatsheetModal').leanModal();
    });
    accessible_modal("#cheatsheetLink", "#cheatsheetModal .close-modal", "#cheatsheetModal", ".content-wrapper");
});
