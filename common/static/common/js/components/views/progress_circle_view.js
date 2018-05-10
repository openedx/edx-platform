(function(define) {
    'use strict';

    define(['backbone',
        'jquery',
        'underscore',
        'gettext',
        'text!../../../templates/components/progress_circle_view.underscore',
        'text!../../../templates/components/progress_circle_segment.underscore'
    ],
        function(
            Backbone,
            $,
            _,
            gettext,
            progressViewTpl,
            progressSegmentTpl
        ) {
            return Backbone.View.extend({
                x: 22,
                y: 22,
                radius: 16,
                degrees: 180,
                strokeWidth: 1.2,

                viewTpl: _.template(progressViewTpl),
                segmentTpl: _.template(progressSegmentTpl),

                initialize: function() {
                    var progress = this.model.get('progress');

                    this.model.set({
                        totalCourses: progress.completed + progress.in_progress + progress.not_started
                    });

                    this.render();
                },

                render: function() {
                    var data = $.extend({}, this.model.toJSON(), {
                        circleSegments: this.getProgressSegments(),
                        x: this.x,
                        y: this.y,
                        radius: this.radius,
                        strokeWidth: this.strokeWidth
                    });

                    this.$el.html(this.viewTpl(data));
                },

                getDegreeIncrement: function(total) {
                    return 360 / total;
                },

                getOffset: function(total) {
                    return 100 - ((1 / total) * 100);
                },

                getProgressSegments: function() {
                    var progressHTML = [],
                        total = this.model.get('totalCourses'),
                        segmentDash = 2 * Math.PI * this.radius,
                        degreeInc = this.getDegreeIncrement(total),
                        data = {
                            // Remove strokeWidth to show a gap between the segments
                            dashArray: segmentDash - this.strokeWidth,
                            degrees: this.degrees,
                            offset: this.getOffset(total),
                            x: this.x,
                            y: this.y,
                            radius: this.radius,
                            strokeWidth: this.strokeWidth
                        },
                        i,
                        segmentData;

                    for (i = 0; i < total; i++) {
                        segmentData = $.extend({}, data, {
                            classList: (i >= this.model.get('progress').completed) ? 'incomplete' : 'complete',
                            degrees: data.degrees + (i * degreeInc)
                        });

                        // Want the incomplete segments to have no gaps
                        if (segmentData.classList === 'incomplete' && (i + 1) < total) {
                            segmentData.dashArray = segmentDash;
                        }

                        progressHTML.push(this.segmentTpl(segmentData));
                    }

                    return progressHTML.join('');
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
