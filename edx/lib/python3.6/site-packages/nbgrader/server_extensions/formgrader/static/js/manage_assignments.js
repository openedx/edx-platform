var Assignment = Backbone.Model.extend({
    idAttribute: 'name',
    urlRoot: base_url + "/formgrader/api/assignment"
});

var Assignments = Backbone.Collection.extend({
    model: Assignment,
    url: base_url + "/formgrader/api/assignments"
});

var AssignmentUI = Backbone.View.extend({

    events: {},

    initialize: function () {
        this.$modal = undefined;
        this.$modal_duedate = undefined;
        this.$modal_timezone = undefined;
        this.$modal_save = undefined;

        this.$name = this.$el.find(".name");
        this.$duedate = this.$el.find(".duedate");
        this.$status = this.$el.find(".status");
        this.$edit = this.$el.find(".edit");
        this.$assign = this.$el.find(".assign");
        this.$preview = this.$el.find(".preview");
        this.$release = this.$el.find(".release");
        this.$collect = this.$el.find(".collect");
        this.$num_submissions = this.$el.find(".num-submissions");

        this.listenTo(this.model, "change", this.render);
        this.listenTo(this.model, "request", this.animateSaving);
        this.listenTo(this.model, "sync", this.closeModal);

        this.render();
    },

    openModal: function () {
        var body = $("<table/>").addClass("table table-striped form-table");
        var name = $("<tr/>");
        body.append(name);
        name.append($("<td/>").addClass("align-middle").text("Name"));
        name.append($("<td/>").append($("<input/>")
            .addClass("modal-name")
            .attr("type", "text")
            .attr("disabled", "disabled")));

        var duedate = $("<tr/>");
        body.append(duedate);
        duedate.append($("<td/>").addClass("align-middle").text("Due date (optional)"));
        duedate.append($("<td/>").append($("<input/>").addClass("modal-duedate").attr("type", "datetime-local")));

        var timezone = $("<tr/>");
        body.append(timezone);
        timezone.append($("<td/>").addClass("align-middle").text("Timezone (optional)"));
        timezone.append($("<td/>").append($("<input/>").addClass("modal-timezone").attr("type", "text")));

        var footer = $("<div/>");
        footer.append($("<button/>")
            .addClass("btn btn-primary save")
            .attr("type", "button")
            .text("Save"));
        footer.append($("<button/>")
            .addClass("btn btn-danger")
            .attr("type", "button")
            .attr("data-dismiss", "modal")
            .text("Cancel"));

        this.$modal = createModal("edit-assignment-modal", "Editing " + this.model.get("name"), body, footer);
        this.$modal.find("input.modal-name").val(this.model.get("name"));
        this.$modal_duedate = this.$modal.find("input.modal-duedate");
        this.$modal_duedate.val(this.model.get("duedate_notimezone"));
        this.$modal_timezone = this.$modal.find("input.modal-timezone");
        this.$modal_timezone.val(this.model.get("duedate_timezone"));
        this.$modal_save = this.$modal.find("button.save");
        this.$modal_save.click(_.bind(this.save, this));
    },

    clear: function () {
        this.$name.empty();
        this.$duedate.empty();
        this.$status.empty();
        this.$edit.empty();
        this.$assign.empty();
        this.$preview.empty();
        this.$release.empty();
        this.$collect.empty();
        this.$num_submissions.empty();
    },

    render: function () {
        this.clear();

        // assignment name
        var name = this.model.get("name")
        this.$name.attr("data-order", name);
        this.$name.append($("<a/>")
            .attr("target", "_blank")
            .attr("href", base_url + "/tree/" + url_prefix + "/" + this.model.get("source_path"))
            .text(name));

        // duedate
        var duedate = this.model.get("duedate");
        var display_duedate = this.model.get("display_duedate");
        if (duedate === null) {
            duedate = "None";
            display_duedate = "None";
        }
        this.$duedate.attr("data-order", duedate);
        this.$duedate.text(display_duedate);

        // status
        var status = this.model.get("status");
        if (status === "draft") {
            this.$status.attr("data-order", "draft");
            this.$status.append($("<span/>").addClass("label label-info").text("draft"));
        } else if (status === "released") {
            this.$status.attr("data-order", "released");
            this.$status.append($("<span/>").addClass("label label-success").text("released"));
        }

        // edit metadata
        this.$edit.append($("<a/>")
            .attr("href", "#")
            .click(_.bind(this.openModal, this))
            .append($("<span/>")
                .addClass("glyphicon glyphicon-pencil")
                .attr("aria-hidden", "true")));

        // generate student version
        this.$assign.append($("<a/>")
            .attr("href", "#")
            .click(_.bind(this.assign, this))
            .append($("<span/>")
                .addClass("glyphicon glyphicon-education")
                .attr("aria-hidden", "true")));

        // preview student version
        var release_path = this.model.get("release_path");
        if (release_path) {
            this.$preview.append($("<a/>")
                .attr("target", "_blank")
                .attr("href", base_url + "/tree/" + url_prefix + "/" + release_path)
                .append($("<span/>")
                    .addClass("glyphicon glyphicon-search")
                    .attr("aria-hidden", "true")));
        }

        // release
        var releaseable = this.model.get("releaseable");
        if (release_path && releaseable) {
            if (status === "draft") {
                this.$release.append($("<a/>")
                    .attr("href", "#")
                    .click(_.bind(this.release, this))
                    .append($("<span/>")
                        .addClass("glyphicon glyphicon-cloud-upload")
                        .attr("aria-hidden", "true")));
            } else {
                this.$release.append($("<a/>")
                    .attr("href", "#")
                    .click(_.bind(this.unrelease, this))
                    .append($("<span/>")
                        .addClass("glyphicon glyphicon-remove")
                        .attr("aria-hidden", "true")));
            }
        }

        // collect
        if (release_path && releaseable) {
            if (status === "released") {
                this.$collect.append($("<a/>")
                    .attr("href", "#")
                    .click(_.bind(this.collect, this))
                    .append($("<span/>")
                        .addClass("glyphicon glyphicon-cloud-download")
                        .attr("aria-hidden", "true")));
            }
        }

        // number of submissions
        var num_submissions = this.model.get("num_submissions");
        this.$num_submissions.attr("data-order", num_submissions);
        if (num_submissions === 0) {
            this.$num_submissions.text(0);
        } else {
            this.$num_submissions.append($("<a/>")
                .attr("href", base_url + "/formgrader/manage_submissions/" + this.model.get("name"))
                .text(num_submissions));
        }
    },

    assign: function () {
        this.clear();
        this.$name.text("Please wait...");
        $.post(base_url + "/formgrader/api/assignment/" + this.model.get("name") + "/assign")
            .done(_.bind(this.assign_success, this))
            .fail(_.bind(this.assign_failure, this));
    },

    assign_success: function (response) {
        this.model.fetch();
        response = JSON.parse(response);
        if (response["success"]) {
            createLogModal(
                "success-modal",
                "Success",
                "Successfully created the student version of '" + this.model.get("name") + "':",
                response["log"]);

        } else {
            createLogModal(
                "error-modal",
                "Error",
                "There was an error creating the student version of '" + this.model.get("name") + "':",
                response["log"],
                response["error"]);
        }
    },

    assign_failure: function (response) {
        this.model.fetch();
        createModal(
            "error-modal",
            "Error",
            "There was an error creating the student version of '" + this.model.get("name") + "'.");
    },

    unrelease: function () {
        this.clear();
        this.$name.text("Please wait...");
        $.post(base_url + "/formgrader/api/assignment/" + this.model.get("name") + "/unrelease")
            .done(_.bind(this.unrelease_success, this))
            .fail(_.bind(this.unrelase_failure, this));
    },

    unrelease_success: function (response) {
        this.model.fetch();
        response = JSON.parse(response);
        if (response["success"]) {
            createLogModal(
                "success-modal",
                "Success",
                "Successfully unreleased '" + this.model.get("name") + "'.",
                response["log"]);

        } else {
            createLogModal(
                "error-modal",
                "Error",
                "There was an error unreleasing '" + this.model.get("name") + "':",
                response["log"],
                response["error"]);
        }
    },

    unrelease_failure: function () {
        this.model.fetch();
        createModal(
            "error-modal",
            "Error",
            "There was an error unreleasing '" + this.model.get("name") + "'.");
    },

    release: function () {
        this.clear();
        this.$name.text("Please wait...");
        $.post(base_url + "/formgrader/api/assignment/" + this.model.get("name") + "/release")
            .done(_.bind(this.release_success, this))
            .fail(_.bind(this.release_failure, this));
    },

    release_success: function (response) {
        this.model.fetch();
        response = JSON.parse(response);
        if (response["success"]) {
            createLogModal(
                "success-modal",
                "Success",
                "Successfully released '" + this.model.get("name") + "'.",
                response["log"]);

        } else {
            createLogModal(
                "error-modal",
                "Error",
                "There was an error releasing '" + this.model.get("name") + "':",
                response["log"],
                response["error"]);
        }
    },

    release_failure: function () {
        this.model.fetch();
        createModal(
            "error-modal",
            "Error",
            "There was an error releasing '" + this.model.get("name") + "'.");
    },

    collect: function () {
        this.clear();
        this.$name.text("Please wait...");
        $.post(base_url + "/formgrader/api/assignment/" + this.model.get("name") + "/collect")
            .done(_.bind(this.collect_success, this))
            .fail(_.bind(this.collect_failure, this));
    },

    collect_success: function (response) {
        this.model.fetch();
        response = JSON.parse(response);
        if (response["success"]) {
            createLogModal(
                "success-modal",
                "Success",
                "Successfully collected submissions of '" + this.model.get("name") + "'.",
                response["log"]);

        } else {
            createLogModal(
                "error-modal",
                "Error",
                "There was an error collecting '" + this.model.get("name") + "':",
                response["log"],
                response["error"]);
        }
    },

    collect_failure: function () {
        this.model.fetch();
        createModal(
            "error-modal",
            "Error",
            "There was an error collecting submissions of '" + this.model.get("name") + "'.");
    },

    save: function () {
        var duedate = this.$modal_duedate.val();
        var timezone = this.$modal_timezone.val();
        if (duedate === "") {
            duedate = null;
            timezone = null;
        }
        this.model.save({"duedate_notimezone": duedate, "duedate_timezone": timezone});
    },

    animateSaving: function () {
        if (this.$modal_save) {
            this.$modal_save.text("Saving...");
        }
    },

    closeModal: function () {
        if (this.$modal) {
            this.$modal.modal('hide')
            this.$modal = undefined;
            this.$modal_duedate = undefined;
            this.$modal_timezone = undefined;
            this.$modal_save = undefined;
        }

        this.render();
    },
});

var insertRow = function (table) {
    var row = $("<tr/>");
    row.append($("<td/>").addClass("name"));
    row.append($("<td/>").addClass("text-center duedate"));
    row.append($("<td/>").addClass("text-center status"));
    row.append($("<td/>").addClass("text-center edit"));
    row.append($("<td/>").addClass("text-center assign"));
    row.append($("<td/>").addClass("text-center preview"));
    row.append($("<td/>").addClass("text-center release"));
    row.append($("<td/>").addClass("text-center collect"));
    row.append($("<td/>").addClass("text-center num-submissions"));
    table.append(row)
    return row;
};

var createAssignmentModal = function () {
    var modal;
    var createAssignment = function () {
        var name = modal.find(".name").val();
        var duedate = modal.find(".duedate").val();
        var timezone = modal.find(".timezone").val();
        if (duedate === "") {
            duedate = null;
            timezone = null;
        }
        if (timezone == "") {
            timezone = null;
        }
        if (name === "") {
            modal.modal('hide');
            return;
        }

        var model = new Assignment({
            "name": name,
            "duedate_notimezone": duedate,
            "duedate_timezone": timezone,
        }, {
            "collection": models
        });

        var tbl = $("#main-table");
        var row = insertRow(tbl);
        var view = new AssignmentUI({
            "model": model,
            "el": row
        });
        views.push(view);
        model.save();
        tbl.parent().DataTable().row.add(row).draw();

        modal.modal('hide');
    };

    var body = $("<table/>").addClass("table table-striped form-table");
    var name = $("<tr/>");
    body.append(name);
    name.append($("<td/>").addClass("align-middle").text("Name"));
    name.append($("<td/>").append($("<input/>").addClass("name").attr("type", "text").attr("size", "31")));

    var duedate = $("<tr/>");
    body.append(duedate);
    duedate.append($("<td/>").addClass("align-middle").text("Due date (optional)"));
    duedate.append($("<td/>").append($("<input/>").addClass("duedate").attr("type", "datetime-local")));

    var timezone = $("<tr/>");
    body.append(timezone);
    timezone.append($("<td/>").addClass("align-middle").text("Timezone (optional)"));
    timezone.append($("<td/>").append($("<input/>").addClass("timezone").attr("type", "text")));

    var footer = $("<div/>");
    footer.append($("<button/>")
        .addClass("btn btn-primary save")
        .attr("type", "button")
        .click(createAssignment)
        .text("Save"));
    footer.append($("<button/>")
        .addClass("btn btn-danger")
        .attr("type", "button")
        .attr("data-dismiss", "modal")
        .text("Cancel"));

    modal = createModal("add-assignment-modal", "Add New Assignment", body, footer);
};

var loadAssignments = function () {
    var tbl = $("#main-table");

    models = new Assignments();
    views = [];
    models.loaded = false;
    models.fetch({
        success: function () {
            tbl.empty();
            models.each(function (model) {
                var view = new AssignmentUI({
                    "model": model,
                    "el": insertRow(tbl)
                });
                views.push(view);
            });
            insertDataTable(tbl.parent());
            models.loaded = true;
        }
    });
};

var models = undefined;
var views = [];
$(window).load(function () {
    loadAssignments();
});
