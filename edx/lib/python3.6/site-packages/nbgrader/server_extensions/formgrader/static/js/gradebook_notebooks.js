var Notebook = Backbone.Model.extend({});
var Notebooks = Backbone.Collection.extend({
    model: Notebook,
    url: base_url + "/formgrader/api/notebooks/" + assignment_id
});

var NotebookUI = Backbone.View.extend({

    events: {},

    initialize: function () {
        this.$name = this.$el.find(".name");
        this.$avg_score = this.$el.find(".avg-score");
        this.$avg_code_score = this.$el.find(".avg-code-score");
        this.$avg_written_score = this.$el.find(".avg-written-score");
        this.$needs_manual_grade = this.$el.find(".needs-manual-grade");

        this.render();
    },

    clear: function () {
        this.$name.empty();
        this.$avg_score.empty();
        this.$avg_code_score.empty();
        this.$avg_written_score.empty();
        this.$needs_manual_grade.empty();
    },

    render: function () {
        this.clear();

        // notebook name
        var name = this.model.get("name");
        this.$name.attr("data-order", name);
        this.$name.append($("<a/>")
            .attr("href", base_url + "/formgrader/gradebook/" + assignment_id + "/" + name)
            .text(name));

        // average score
        var score = roundToPrecision(this.model.get("average_score"), 2);
        var max_score = roundToPrecision(this.model.get("max_score"), 2);
        if (max_score === 0) {
            this.$avg_score.attr("data-order", 0.0);
        } else {
            this.$avg_score.attr("data-order", score / max_score);
        }
        this.$avg_score.text(score + " / " + max_score);

        // average code score
        score = roundToPrecision(this.model.get("average_code_score"), 2);
        max_score = roundToPrecision(this.model.get("max_code_score"), 2);
        if (max_score === 0) {
            this.$avg_code_score.attr("data-order", 0.0);
        } else {
            this.$avg_code_score.attr("data-order", score / max_score);
        }
        this.$avg_code_score.text(score + " / " + max_score);

        // average written score
        score = roundToPrecision(this.model.get("average_written_score"), 2);
        max_score = roundToPrecision(this.model.get("max_written_score"), 2);
        if (max_score === 0) {
            this.$avg_written_score.attr("data-order", 0.0);
        } else {
            this.$avg_written_score.attr("data-order", score / max_score);
        }
        this.$avg_written_score.text(score + " / " + max_score);

        // needs manual grade
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
    row.append($("<td/>").addClass("text-center avg-score"));
    row.append($("<td/>").addClass("text-center avg-code-score"));
    row.append($("<td/>").addClass("text-center avg-written-score"));
    row.append($("<td/>").addClass("text-center needs-manual-grade"));
    table.append(row)
    return row;
};

var loadNotebooks = function () {
    var tbl = $("#main-table");

    models = new Notebooks();
    views = [];
    models.loaded = false;
    models.fetch({
        success: function () {
            tbl.empty();
            models.each(function (model) {
                var view = new NotebookUI({
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
    loadNotebooks();
});
