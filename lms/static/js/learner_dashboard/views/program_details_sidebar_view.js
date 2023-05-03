/* globals gettext */

import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';
import StringUtils from 'edx-ui-toolkit/js/utils/string-utils';

import CertificateView from './certificate_list_view';
import ProgramProgressView from './progress_circle_view';

import sidebarTpl from '../../../templates/learner_dashboard/program_details_sidebar.underscore';

class ProgramDetailsSidebarView extends Backbone.View {
    constructor(options) {
        const defaults = {
            events: {
                'click .pathway-button': 'trackPathwayClicked',
            },
        };
        super(Object.assign({}, defaults, options));
    }

    initialize(options) {
        this.tpl = HtmlUtils.template(sidebarTpl);
        this.courseModel = options.courseModel || {};
        this.certificateCollection = options.certificateCollection || [];
        this.programCertificate = this.getProgramCertificate();
        this.programRecordUrl = options.programRecordUrl;
        this.industryPathways = options.industryPathways;
        this.creditPathways = options.creditPathways;
        this.programModel = options.model;
        this.programTabViewEnabled =  options.programTabViewEnabled;
        this.render();
    }

    render() {
        const data = $.extend({}, this.model.toJSON(), {
            programCertificate: this.programCertificate ?
                this.programCertificate.toJSON() : {},
            programRecordUrl: this.programRecordUrl,
            industryPathways: this.industryPathways,
            creditPathways: this.creditPathways,
            programTabViewEnabled: this.programTabViewEnabled
        });

        HtmlUtils.setHtml(this.$el, this.tpl(data));
        this.postRender();
    }

    postRender() {
        if (!this.programCertificate) {
            this.progressModel = new Backbone.Model({
                title: StringUtils.interpolate(
                    gettext('{type} Progress'),
                    { type: this.model.get('type') },
                ),
                label: gettext('Earned Certificates'),
                progress: {
                    completed: this.courseModel.get('completed').length,
                    in_progress: this.courseModel.get('in_progress').length,
                    not_started: this.courseModel.get('not_started').length,
                },
            });

            this.programProgressView = new ProgramProgressView({
                el: '.js-program-progress',
                model: this.progressModel,
            });
        }

        if (this.certificateCollection.length) {
            this.certificateView = new CertificateView({
                el: '.js-course-certificates',
                collection: this.certificateCollection,
                title: gettext('Earned Certificates'),
            });
        }
    }

    getProgramCertificate() {
        const certificate = this.certificateCollection.findWhere({ type: 'program' });
        const base = '/static/images/programs/program-certificate-';

        if (certificate) {
            certificate.set({
                img: `${base + this.getType()}.gif`,
            });
        }

        return certificate;
    }

    getType() {
        const type = this.model.get('type').toLowerCase();

        return type.replace(/\s+/g, '-');
    }

    trackPathwayClicked(event) {
        const button = event.currentTarget;

        window.analytics.track('edx.bi.dashboard.program.pathway.clicked', {
            category: 'pathways',
            // Credentials uses the uuid without dashes so we are converting here for consistency
            program_uuid: this.programModel.attributes.uuid.replace(/-/g, ''),
            program_name: this.programModel.attributes.title,
            pathway_link_uuid: $(button).data('pathwayUuid').replace(/-/g, ''),
            pathway_name: $(button).data('pathwayName'),
        });
    }
}

export default ProgramDetailsSidebarView;
