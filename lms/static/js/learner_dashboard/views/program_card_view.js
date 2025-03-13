/* globals gettext */

import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';

import programCardTpl from '../../../templates/learner_dashboard/program_card.underscore';

class ProgramCardView extends Backbone.View {
    constructor(options) {
        const defaults = {
            className: 'program-card',
            attributes: function attr() {
                return {
                    'aria-labelledby': `program-${this.model.get('uuid')}`,
                    role: 'group',
                };
            },
        };
        // eslint-disable-next-line prefer-object-spread
        super(Object.assign({}, defaults, options));
    }

    initialize({ context }) {
        this.tpl = HtmlUtils.template(programCardTpl);
        this.progressCollection = context.progressCollection;
        if (this.progressCollection) {
            this.progressModel = this.progressCollection.findWhere({
                uuid: this.model.get('uuid'),
            });
        }
        this.render();
    }

    render() {
        const orgList = this.model.get('authoring_organizations').map(org => gettext(org.key));
        // eslint-disable-next-line no-undef
        const data = $.extend(
            this.model.toJSON(),
            this.getProgramProgress(),
            {
                orgList: orgList.join(' '),
            },
        );

        HtmlUtils.setHtml(this.$el, this.tpl(data));
    }

    // Calculate counts for progress and percentages for styling
    getProgramProgress() {
        const progress = this.progressModel ? this.progressModel.toJSON() : false;

        if (progress) {
            progress.total = progress.completed
        + progress.in_progress
        + progress.not_started;

            progress.percentage = {
                completed: ProgramCardView.getWidth(progress.completed, progress.total),
                in_progress: ProgramCardView.getWidth(progress.in_progress, progress.total),
            };
        }

        return {
            progress,
        };
    }

    static getWidth(val, total) {
        const int = (val / total) * 100;
        return `${int}%`;
    }
}

export default ProgramCardView;
