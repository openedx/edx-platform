var StudentSubmission = Backbone.Model.extend({});
var StudentSubmissions = Backbone.Collection.extend({
    model: StudentSubmission,
    url: base_url + "/formgrader/api/student_submissions/" + student_id
});

var StudentSubmissionUI = Backbone.View.extend({

    events: {},

    initialize: function () {
        this.$name = this.$el.find(".name");
        this.$score = this.$el.find(".score");
        this.$code_score = this.$el.find(".code-score");
        this.$written_score = this.$el.find(".written-score");
        this.$needs_manual_grade = this.$el.find(".needs-manual-grade");

        this.render();
    },

    clear: function () {
        this.$name.empty();
        this.$score.empty();
        this.$code_score.empty();
        this.$written_score.empty();
        this.$needs_manual_grade.empty();
    },

    render: function () {
        this.clear();

        // name
        var name = this.model.get("name");
        this.$name.attr("data-order", name);
        if (!this.model.get("submitted")) {
            this.$name.text(name + " (no submission)");
        } else if (!this.model.get("autograded")) {
            this.$name.text(name + " (not autograded)");
        } else {
            this.$name.append($("<a/>")
                .attr("href", base_url + "/formgrader/manage_students/" + student_id + "/" + name)
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
        var code_score = roundToPrecision(this.model.get("code_score"), 2);
        var max_code_score = roundToPrecision(this.model.get("max_code_score"), 2);
        if (max_code_score === 0) {
            this.$code_score.attr("data-order", 0.0);
        } else {
            this.$code_score.attr("data-order", code_score / max_code_score);
        }
        this.$code_score.text(code_score + " / " + max_code_score);

        // written score
        var written_score = roundToPrecision(this.model.get("written_score"), 2);
        var max_written_score = roundToPrecision(this.model.get("max_written_score"), 2);
        if (max_written_score === 0) {
            this.$written_score.attr("data-order", 0.0);
        } else {
            this.$written_score.attr("data-order", written_score / max_written_score);
        }
        this.$written_score.text(written_score + " / " + max_written_score);

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
    },
});

var insertRow = function (table) {
    var row = $("<tr/>");
    row.append($("<td/>").addClass("name"));
    row.append($("<td/>").addClass("text-center score"));
    row.append($("<td/>").addClass("text-center code-score"));
    row.append($("<td/>").addClass("text-center written-score"));
    row.append($("<td/>").addClass("text-center needs-manual-grade"));
    table.append(row)
    return row;
};

var loadStudentSubmissions = function () {
    var tbl = $("#main-table");

    models = new StudentSubmissions();
    views = [];
    models.loaded = false;
    models.fetch({
        success: function () {
            tbl.empty();
            models.each(function (model) {
                var view = new StudentSubmissionUI({
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
    loadStudentSubmissions();
});
