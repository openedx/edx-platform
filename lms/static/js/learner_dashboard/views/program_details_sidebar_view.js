(function(define) {
    'use strict';

    define([
        'backbone',
        'jquery',
        'underscore',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils',
        'edx-ui-toolkit/js/utils/string-utils',
        'common/js/components/views/progress_circle_view',
        'js/learner_dashboard/views/certificate_list_view',
        'text!../../../templates/learner_dashboard/program_details_sidebar.underscore'
    ],
        function(
            Backbone,
            $,
            _,
            gettext,
            HtmlUtils,
            StringUtils,
            ProgramProgressView,
            CertificateView,
            sidebarTpl
        ) {
            return Backbone.View.extend({
                tpl: HtmlUtils.template(sidebarTpl),

                initialize: function(options) {
                    this.courseModel = options.courseModel || {};
                    this.certificateCollection = options.certificateCollection || [];
                    this.programCertificate = this.getProgramCertificate();
                    this.render();
                },

                render: function() {
                    var data = $.extend({}, this.model.toJSON(), {
                        programCertificate: this.programCertificate ?
                                            this.programCertificate.toJSON() : {}
                    });

                    HtmlUtils.setHtml(this.$el, this.tpl(data));
                    this.postRender();
                },

                postRender: function() {
                    if (!this.programCertificate) {
                        this.progressModel = new Backbone.Model({
                            title: StringUtils.interpolate(
                                gettext('{type} Progress'),
                                {type: this.model.get('type')}
                            ),
                            label: gettext('Earned Certificates'),
                            progress: {
                                completed: this.courseModel.get('completed').length,
                                in_progress: this.courseModel.get('in_progress').length,
                                not_started: this.courseModel.get('not_started').length
                            }
                        });

                        this.programProgressView = new ProgramProgressView({
                            el: '.js-program-progress',
                            model: this.progressModel
                        });
                    }

                    if (this.certificateCollection.length) {
                        this.certificateView = new CertificateView({
                            el: '.js-course-certificates',
                            collection: this.certificateCollection,
                            title: gettext('Earned Certificates')
                        });
                    }
                },

                getProgramCertificate: function() {
                    var certificate = this.certificateCollection.findWhere({type: 'program'}),
                        base = '/static/images/programs/program-certificate-';

                    if (certificate) {
                        certificate.set({
                            img: base + this.getType() + '.gif'
                        });
                    }

                    return certificate;
                },

                getType: function() {
                    var type = this.model.get('type').toLowerCase();

                    return type.replace(/\s+/g, '-');
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
