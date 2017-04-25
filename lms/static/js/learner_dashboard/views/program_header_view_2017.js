(function(define) {
    'use strict';

    define(['backbone',
        'jquery',
        'edx-ui-toolkit/js/utils/html-utils',
        'text!../../../templates/learner_dashboard/program_header_view_2017.underscore',
        'text!../../../images/programs/micromasters-program-details.svg',
        'text!../../../images/programs/xseries-program-details.svg',
        'text!../../../images/programs/professional-certificate-program-details.svg'
    ],
         function(Backbone, $, HtmlUtils, pageTpl, MicroMastersLogo,
                  XSeriesLogo, ProfessionalCertificateLogo) {
             return Backbone.View.extend({
                 breakpoints: {
                     min: {
                         medium: '768px',
                         large: '1180px'
                     }
                 },

                 el: '.js-program-header',

                 tpl: HtmlUtils.template(pageTpl),

                 initialize: function() {
                     this.render();
                 },

                 getLogo: function() {
                     var logo = false,
                         type = this.model.get('programData').type;

                     if (type === 'MicroMasters') {
                         logo = MicroMastersLogo;
                     } else if (type === 'XSeries') {
                         logo = XSeriesLogo;
                     } else if (type === 'Professional Certificate') {
                         logo = ProfessionalCertificateLogo;
                     }
                     return logo;
                 },

                 render: function() {
                     var data = $.extend(this.model.toJSON(), {
                         breakpoints: this.breakpoints,
                         logo: this.getLogo()
                     });

                     if (this.model.get('programData')) {
                         HtmlUtils.setHtml(this.$el, this.tpl(data));
                     }
                 }
             });
         }
    );
}).call(this, define || RequireJS.define);
