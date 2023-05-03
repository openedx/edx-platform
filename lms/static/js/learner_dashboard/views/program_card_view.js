/* globals gettext */

import Backbone from 'backbone';
import picturefill from 'picturefill';

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
        super(Object.assign({}, defaults, options));
    }

    initialize(data) {
        this.tpl = HtmlUtils.template(programCardTpl);
        this.progressCollection = data.context.progressCollection;
        if (this.progressCollection) {
            this.progressModel = this.progressCollection.findWhere({
                uuid: this.model.get('uuid'),
            });
        }
        this.render();
    }

    render() {
        const orgList = this.model.get('authoring_organizations').map(org => gettext(org.key));
        const data = $.extend(
            this.model.toJSON(),
            this.getProgramProgress(),
            { orgList: orgList.join(' ') },
        );

        HtmlUtils.setHtml(this.$el, this.tpl(data));
        this.postRender();
    }

    postRender() {
        if (navigator.userAgent.indexOf('MSIE') !== -1 ||
        navigator.appVersion.indexOf('Trident/') > 0) {
            /* Microsoft Internet Explorer detected in. */
            window.setTimeout(() => {
                this.reLoadBannerImage();
            }, 100);
        }
    }

    // Calculate counts for progress and percentages for styling
    getProgramProgress() {
        const progress = this.progressModel ? this.progressModel.toJSON() : false;

        if (progress) {
            progress.total = progress.completed +
        progress.in_progress +
        progress.not_started;

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

    // Defer loading the rest of the page to limit FOUC
    reLoadBannerImage() {
        const $img = this.$('.program_card .banner-image');
        const imgSrcAttr = $img ? $img.attr('src') : {};

        if (!imgSrcAttr || imgSrcAttr.length < 0) {
            try {
                ProgramCardView.reEvaluatePicture();
            } catch (err) {
                // Swallow the error here
            }
        }
    }

    static reEvaluatePicture() {
        picturefill({
            reevaluate: true,
        });
    }
}

export default ProgramCardView;
