var Submission = Backbone.Model.extend({
    idAttribute: 'student',
    urlRoot: base_url + "/formgrader/api/submission/" + assignment_id
});

var Submissions = Backbone.Collection.extend({
    model: Submission,
    url: base_url + "/formgrader/api/submissions/" + assignment_id
});

var SubmissionUI = Backbone.View.extend({

    events: {},

    initialize: function () {
        this.$student_name = this.$el.find(".student-name");
        this.$student_id = this.$el.find(".student-id");
        this.$timestamp = this.$el.find(".timestamp");
        this.$status = this.$el.find(".status");
        this.$score = this.$el.find(".score");
        this.$autograde = this.$el.find(".autograde");

        this.listenTo(this.model, "sync", this.render);

        this.render();
    },

    clear: function () {
        this.$student_name.empty();
        this.$student_id.empty();
        this.$timestamp.empty();
        this.$status.empty();
        this.$score.empty();
        this.$autograde.empty();
    },

    render: function () {
        this.clear();

        var student = this.model.get("student");
        var assignment = this.model.get("name");

        // student name
        var last_name = this.model.get("last_name");
        var first_name = this.model.get("first_name");
        if (last_name === null) last_name = "None";
        if (first_name === null) first_name = "None";
        var name = last_name + ", " + first_name;
        this.$student_name.attr("data-order", name);
        if (this.model.get("autograded")) {
            this.$student_name.append($("<a/>")
                .attr("href", base_url + "/formgrader/manage_students/" + student + "/" + assignment)
                .text(name));
        } else {
            this.$student_name.text(name);
        }

        // student id
        this.$student_id.attr("data-order", student);
        this.$student_id.text(student);

        // timestamp
        var timestamp = this.model.get("timestamp");
        var display_timestamp = this.model.get("display_timestamp");
        if (timestamp === null) {
            timestamp = "None";
            display_timestamp = "None";
        }
        this.$timestamp.attr("data-order", timestamp);
        this.$timestamp.text(display_timestamp);

        // status
        if (!this.model.get("autograded")) {
            this.$status.attr("data-order", 0);
            this.$status.append($("<span/>")
                .addClass("label label-warning")
                .text("needs autograding"));
        } else if (this.model.get("needs_manual_grade")) {
            this.$status.attr("data-order", 1);
            this.$status.append($("<span/>")
                .addClass("label label-info")
                .text("needs manual grading"));
        } else {
            this.$status.attr("data-order", 2);
            this.$status.append($("<span/>")
                .addClass("label label-success")
                .text("graded"));
        }

        // score
        if (this.model.get("autograded")) {
            var score = roundToPrecision(this.model.get("score"), 2);
            var max_score = roundToPrecision(this.model.get("max_score"), 2);
            if (max_score === 0) {
                this.$score.attr("data-order", 0.0);
            } else {
                this.$score.attr("data-order", score / max_score);
            }
            this.$score.text(score + " / " + max_score);
        } else {
            this.$score.attr("data-order", 0.0);
        }

        // autograde
        this.$autograde.append($("<a/>")
            .attr("href", "#")
            .click(_.bind(this.autograde, this))
            .append($("<span/>")
                .addClass("glyphicon glyphicon-flash")
                .attr("aria-hidden", "true")));
    },

    autograde: function () {
        this.clear();
        this.$student_name.text("Please wait...");
        var student = this.model.get("student");
        var assignment = this.model.get("name");
        $.post(base_url + "/formgrader/api/submission/" + assignment + "/" + student + "/autograde")
            .done(_.bind(this.autograde_success, this))
            .fail(_.bind(this.autograde_failure, this));
    },

    autograde_success: function (response) {
        this.model.fetch();
        response = JSON.parse(response);
        var student = this.model.get("student");
        var assignment = this.model.get("name");
        if (response["success"]) {
            createLogModal(
                "success-modal",
                "Success",
                "Successfully autograded '" + assignment + "' for student '" + student + "'.",
                response["log"]);

        } else {
            createLogModal(
                "error-modal",
                "Error",
                "There was an error autograding '" + assignment + "' for student '" + student + "':",
                response["log"],
                response["error"]);
        }
    },

    autograde_failure: function (response) {
        this.model.fetch();
        var student = this.model.get("student");
        var assignment = this.model.get("name");
        createModal(
            "error-modal",
            "Error",
            "There was an error autograding '" + assignment + "' for student '" + student + "'.");
    },
});

var insertRow = function (table) {
    var row = $("<tr/>");
    row.append($("<td/>").addClass("student-name"));
    row.append($("<td/>").addClass("text-center student-id"));
    row.append($("<td/>").addClass("text-center timestamp"));
    row.append($("<td/>").addClass("text-center status"));
    row.append($("<td/>").addClass("text-center score"));
    row.append($("<td/>").addClass("text-center autograde"));
    table.append(row)
    return row;
};

var loadSubmissions = function () {
    var tbl = $("#main-table");

    models = new Submissions();
    views = [];
    models.loaded = false;
    models.fetch({
        success: function () {
            tbl.empty();
            models.each(function (model) {
                var view = new SubmissionUI({
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
    loadSubmissions();
});
