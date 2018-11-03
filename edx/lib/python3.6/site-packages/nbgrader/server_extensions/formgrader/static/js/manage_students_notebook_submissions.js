var StudentSubmittedNotebook = Backbone.Model.extend({});
var StudentSubmittedNotebooks = Backbone.Collection.extend({
    model: StudentSubmittedNotebook,
    url: base_url + "/formgrader/api/student_notebook_submissions/" + student_id + "/" + assignment_id
});

var StudentSubmittedNotebookUI = Backbone.View.extend({

    events: {},

    initialize: function () {
        this.$name = this.$el.find(".name");
        this.$score = this.$el.find(".score");
        this.$code_score = this.$el.find(".code-score");
        this.$written_score = this.$el.find(".written-score");
        this.$needs_manual_grade = this.$el.find(".needs-manual-grade");
        this.$tests_failed = this.$el.find(".tests-failed");
        this.$flagged = this.$el.find(".flagged");

        this.render();
    },

    clear: function () {
        this.$name.empty();
        this.$score.empty();
        this.$code_score.empty();
        this.$written_score.empty();
        this.$needs_manual_grade.empty();
        this.$tests_failed.empty();
        this.$flagged.empty();
    },

    render: function () {
        this.clear();

        // notebook name
        var name = this.model.get("name");
        this.$name.attr("data-order", name);
        if (this.model.get("id") === null) {
            this.$name.append(name + " (file missing)");
        } else {
            this.$name.append($("<a/>")
                .attr("href", base_url + "/formgrader/submissions/" + this.model.get("id"))
                .text(name));
        }

        // score
        var score = roundToPrecision(this.model.get("score"), 2);
        var max_score = roundToPrecision(this.model.get("max_score"), 2);
        if (max_score === 0) {
            this.$score.attr("data-order", 0.0);
        } else {
            this.$score.attr("data-order", score / max_score);
        }
        this.$score.text(score + " / " + max_score);

        // code score
        score = roundToPrecision(this.model.get("code_score"), 2);
        max_score = roundToPrecision(this.model.get("max_code_score"), 2);
        if (max_score === 0) {
            this.$code_score.attr("data-order", 0.0);
        } else {
            this.$code_score.attr("data-order", score / max_score);
        }
        this.$code_score.text(score + " / " + max_score);

        // written score
        score = roundToPrecision(this.model.get("written_score"), 2);
        max_score = roundToPrecision(this.model.get("max_written_score"), 2);
        if (max_score === 0) {
            this.$written_score.attr("data-order", 0.0);
        } else {
            this.$written_score.attr("data-order", score / max_score);
        }
        this.$written_score.text(score + " / " + max_score);

        // needs manual grade?
        if (this.model.get("needs_manual_grade")) {
            this.$needs_manual_grade.attr("data-search", "needs manual grade");
            this.$needs_manual_grade.attr("data-order", 1);
            this.$needs_manual_grade.append($("<span/>")
                .addClass("glyphicon glyphicon-ok"));
        } else {
            this.$needs_manual_grade.attr("data-search", "");
            this.$needs_manual_grade.attr("data-order", 0);
        }

        // tests failed?
        if (this.model.get("failed_tests")) {
            this.$tests_failed.attr("data-search", "tests failed");
            this.$tests_failed.attr("data-order", 1);
            this.$tests_failed.append($("<span/>")
                .addClass("glyphicon glyphicon-ok"));
        } else {
            this.$tests_failed.attr("data-search", "");
            this.$tests_failed.attr("data-order", 0);
        }

        // flagged?
        if (this.model.get("flagged")) {
            this.$flagged.attr("data-search", "flagged");
            this.$flagged.attr("data-order", 1);
            this.$flagged.append($("<span/>")
                .addClass("glyphicon glyphicon-flag"));
        } else {
            this.$flagged.attr("data-search", "");
            this.$flagged.attr("data-order", 0);
        }
    },
});

var insertRow = function (table) {
    var row = $("<tr/>");
    row.append($("<td/>").addClass("name"));
    row.append($("<td/>").addClass("text-center score"));
    row.append($("<td/>").addClass("text-center code-score"));
    row.append($("<td/>").addClass("text-center written-score"));
    row.append($("<td/>").addClass("text-center needs-manual-grade"));
    row.append($("<td/>").addClass("text-center tests-failed"));
    row.append($("<td/>").addClass("text-center flagged"));
    table.append(row)
    return row;
};

var loadStudentSubmittedNotebooks = function () {
    var tbl = $("#main-table");

    models = new StudentSubmittedNotebooks();
    views = [];
    models.loaded = false;
    models.fetch({
        success: function () {
            tbl.empty();
            models.each(function (model) {
                var view = new StudentSubmittedNotebookUI({
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
    loadStudentSubmittedNotebooks();
});
