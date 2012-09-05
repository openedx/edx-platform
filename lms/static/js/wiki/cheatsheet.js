$(document).ready(function () {
    $('#cheatsheetLink').click(function() {
        $('#cheatsheetModal').modal('show');
    });
    
    $('#cheatsheetModal .close-btn').click(function(e) {
        $('#cheatsheetModal').modal('hide');
    });
});