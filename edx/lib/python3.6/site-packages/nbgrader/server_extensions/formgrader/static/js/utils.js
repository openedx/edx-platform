var createModal = function (id, title, body, footer) {
    var modal = $("<div/>")
        .addClass("modal")
        .addClass("fade")
        .attr("id", id)
        .attr("role", "dialog")

    var dialog = $("<div/>").addClass("modal-dialog");
    modal.append(dialog);

    var content = $("<div/>").addClass("modal-content");
    dialog.append(content);

    var header = $("<div/>").addClass("modal-header");
    content.append(header);
    header.append($("<button/>")
        .addClass("close")
        .attr("data-dismiss", "modal")
        .attr("aria-label", "Close")
        .append($("<span/>")
            .attr("aria-hidden", "true")
            .html("&times;")));
    header.append($("<h4/>")
        .addClass("modal-title")
        .text(title));

    content.append($("<div/>").addClass("modal-body").append(body));

    if (!footer) {
        footer = $("<div/>");
        footer.append($("<button/>")
            .addClass("btn btn-primary close")
            .attr("type", "button")
            .attr("data-dismiss", "modal")
            .text("OK"));
    }
    content.append($("<div/>").addClass("modal-footer").append(footer));

    // remove the modal on close
    modal.on("hidden.bs.modal", function () {
        modal.remove();
    });

    $("body").append(modal);
    modal.modal();
    return modal;
};

var createLogModal = function (id, title, message, log, error) {
    var body = $("<div>");
    body.append($("<p/>").text(message));

    if (log) {
        var log_panel = $("<div/>").addClass("panel panel-warning");
        log_panel.append($("<div/>").addClass("panel-heading").text("Log Output"));
        log_panel.append($("<div/>")
            .addClass("panel-body")
            .append($("<pre/>").text(log)));
        body.append(log_panel);
    }

    if (error) {
        var err_panel = $("<div/>").addClass("panel panel-danger");
        err_panel.append($("<div/>").addClass("panel-heading").text("Traceback"));
        err_panel.append($("<div/>")
            .addClass("panel-body")
            .append($("<pre/>").text(error)));
        body.append(err_panel);
    }

    return createModal(id, title, body);
};

var roundToPrecision = function (num, precision) {
    var factor = Math.pow(10, precision);
    return Math.round(num * factor) / factor;
};

var insertDataTable = function (tbl) {
    tbl.DataTable({
        info: false,
        paging: false,
        saveState: true,
        columnDefs: [{
            "targets": "no-sort",
            "orderable": false
        }]
    });
};
