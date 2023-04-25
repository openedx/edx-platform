import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';

import progressViewTpl from '../../../templates/learner_dashboard//progress_circle_view.underscore';
import progressSegmentTpl from '../../../templates/learner_dashboard/progress_circle_segment.underscore';

class ProgressCircleView extends Backbone.View {
    initialize() {
        this.x = 22;
        this.y = 22;
        this.radius = 16;
        this.degrees = 180;
        this.strokeWidth = 1.2;

        this.viewTpl = HtmlUtils.template(progressViewTpl);
        this.segmentTpl = HtmlUtils.template(progressSegmentTpl);

        const progress = this.model.get('progress');

        this.model.set({
            totalCourses: progress.completed + progress.in_progress + progress.not_started,
        });

        this.render();
    }

    render() {
        const data = $.extend({}, this.model.toJSON(), {
            circleSegments: this.getProgressSegments(),
            x: this.x,
            y: this.y,
            radius: this.radius,
            strokeWidth: this.strokeWidth,
        });

        HtmlUtils.setHtml(this.$el, this.viewTpl(data));
    }

    static getDegreeIncrement(total) {
        return 360 / total;
    }

    static getOffset(total) {
        return 100 - ((1 / total) * 100);
    }

    getProgressSegments() {
        const progressHTML = [];
        const total = this.model.get('totalCourses');
        const segmentDash = 2 * Math.PI * this.radius;
        const degreeInc = ProgressCircleView.getDegreeIncrement(total);
        const data = {
            // Remove strokeWidth to show a gap between the segments
            dashArray: segmentDash - this.strokeWidth,
            degrees: this.degrees,
            offset: ProgressCircleView.getOffset(total),
            x: this.x,
            y: this.y,
            radius: this.radius,
            strokeWidth: this.strokeWidth,
        };

        for (let i = 0; i < total; i += 1) {
            const segmentData = $.extend({}, data, {
                classList: (i >= this.model.get('progress').completed) ? 'incomplete' : 'complete',
                degrees: data.degrees + (i * degreeInc),
            });

            // Want the incomplete segments to have no gaps
            if (segmentData.classList === 'incomplete' && (i + 1) < total) {
                segmentData.dashArray = segmentDash;
            }

            progressHTML.push(this.segmentTpl(segmentData));
        }

        return progressHTML.join('');
    }
}

export default ProgressCircleView;
