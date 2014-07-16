/**
 * The EditXBlockModal is a Backbone view that shows an xblock editor in a modal window.
 * It is invoked using the edit method which is passed an existing rendered xblock,
 * and upon save an optional refresh function can be invoked to update the display.
 */
define(["jquery", "underscore", "gettext", "js/views/modals/base_modal",
    "js/models/xblock_info", "date", "js/views/utils/xblock_utils",
    "js/collections/course_grader", "js/views/overview_assignment_grader",
    "js/utils/get_date"],
    function($, _, gettext, BaseModal, XBlockInfo, date, XBlockViewUtils,
        CourseGraderCollection, OverviewAssignmentGrader,
        DateUtils) {
        var EditSectionXBlockModal = BaseModal.extend({
            events : {
                "click .action-save": "save",
                "click .action-modes a": "changeMode"
            },

            options: $.extend({}, BaseModal.prototype.options, {
                modalName: 'edit-xblock',
                addSaveButton: true,
                title: 'Subsection Settings',
                modalSize: 'med'
            }),

            initialize: function() {
                BaseModal.prototype.initialize.call(this);
                this.events = _.extend({}, BaseModal.prototype.events, this.events);
                this.template = this.loadTemplate('edit-section-xblock-modal');
                this.xblockInfo = this.options.model;
                this.date = date;
                this.graderTypes = new CourseGraderCollection(JSON.parse(this.xblockInfo.get('course_graders')), {parse:true});
                this.SelectGraderView = OverviewAssignmentGrader.extend({
                   selectGradeType : function(e) {
                      e.preventDefault();
                      this.removeMenu(e);
                      this.assignmentGrade.set('graderType', ($(e.target).hasClass('gradable-status-notgraded')) ? 'notgraded' : $(e.target).text());
                      this.render();
                    }
                })
            },


            getDateTime: function(datetime) {
                var formatted_date, formatted_time;

                formatted_date = this.date.parse(datetime.split(' at ')[0]).toString('mm/dd/yy');
                formatted_time = this.date.parse(datetime.split(' at ')[1].split('UTC')[0]).toString('hh:mm');

                return {
                    'date': formatted_date,
                    'time': formatted_time,
                }
            },


            getContentHtml: function() {
                return this.template({
                    xblockInfo: this.xblockInfo,
                    getDateTime: this.getDateTime,
                    date: this.date,
                });
            },


            render: function() {
                BaseModal.prototype.render.call(this);
                this.$el.find('.date').datepicker({'dateFormat': 'm/d/yy'});
                this.$el.find('.time').timepicker({'timeFormat' : 'H:i'});
                new this.SelectGraderView({
                    el : this.$el.find('.gradable-status'),
                    graders : this.graderTypes,
                    hideSymbol : true,
                 });

                function removeDateSetter(e) {
                    e.preventDefault();
                    var $block = $(this).closest('.due-date-input');
                    $block.find('.date').val('');
                    $block.find('.time').val('');
                }

                function syncReleaseDate(e) {
                    e.preventDefault();
                    $("#start_date").val("");
                    $("#start_time").val("");
                }

                this.$el.find('.remove-date').bind('click', removeDateSetter);
                this.$el.find('.sync-date').bind('click', syncReleaseDate);
            },


            save: function(event) {
                event.preventDefault();
                var releaseDatetime = DateUtils(
                    $('.edit-section-modal #start_date'),
                    $('.edit-section-modal #start_time')
                );
                // Check releaseDatetime and dueDatetime for sanity?
                 var metadata = {
                     'release_date': releaseDatetime,
                };
                if (this.xblockInfo.get('category') === 'sequential') {
                    var dueDatetime = DateUtils(
                        $('.edit-section-modal #due_date'),
                        $('.edit-section-modal #due_time')
                    );
                    metadata.due_date = dueDatetime;
                    format = $('.edit-section-modal .gradable .gradable-status .status-label')[0].firstChild.textContent;
                    metadata.format = format;
                }
                XBlockViewUtils.updateXBlockFields(this.xblockInfo, {metadata: metadata}, true).done(
                    this.options.onSave
                );
                this.hide()
            },

        });

        return EditSectionXBlockModal;
    });
