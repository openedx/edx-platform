var Assignment = Backbone.Model.extend({});
var Assignments = Backbone.Collection.extend({
    model: Assignment,
    url: base_url + "/formgrader/api/assignments"
});

var AssignmentUI = Backbone.View.extend({

    events: {},

    initialize: function () {
        this.$name = this.$el.find(".name");
        this.$duedate = this.$el.find(".duedate");
        this.$num_submissions = this.$el.find(".num-submissions");
        this.$score = this.$el.find(".score");

        this.render();
    },

    clear: function () {
        this.$name.empty();
        this.$duedate.empty();
        this.$num_submissions.empty();
        this.$score.empty();
    },

    render: function () {
        this.clear();

        // assignment name
        var name = this.model.get("name");
        this.$name.attr("data-order", name);
        this.$name.append($("<a/>")
            .attr("href", base_url + "/formgrader/gradebook/" + name)
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

        // number of submissions
        var num_submissions = this.model.get("num_submissions");
        this.$num_submissions.attr("data-order", num_submissions)
        this.$num_submissions.text(num_submissions);

        // score
        var score = roundToPrecision(this.model.get("average_score"), 2);
        var max_score = roundToPrecision(this.model.get("max_score"), 2);
        if (max_score === 0) {
            this.$score.attr("data-order", 0.0)
        } else {
            this.$score.attr("data-order", score / max_score);
        }
        this.$score.text(score + " / " + max_score);

    },
});

var insertRow = function (table) {
    var row = $("<tr/>");
    row.append($("<td/>").addClass("name"));
    row.append($("<td/>").addClass("text-center duedate"));
    row.append($("<td/>").addClass("text-center num-submissions"));
    row.append($("<td/>").addClass("text-center score"));
    table.append(row)
    return row;
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
