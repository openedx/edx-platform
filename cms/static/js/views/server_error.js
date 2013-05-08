CMS.ServerError = function(model, error) {
    var m = new CMS.Models.Alert({
        "type": "error",
        "title": "Server Error",
        "message": error.responseText,
        "close": true
    });
    new CMS.Views.Alert({model: m}).render();
};
