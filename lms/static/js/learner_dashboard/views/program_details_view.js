/* globals gettext */

import Backbone from 'backbone';

import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';

import CollectionListView from './collection_list_view';
import CourseCardCollection from '../collections/course_card_collection';
import CourseCardView from './course_card_view';
import HeaderView from './program_header_view';
import SidebarView from './program_details_sidebar_view';

import pageTpl from '../../../templates/learner_dashboard/program_details_view.underscore';
import trackECommerceEvents from '../../commerce/track_ecommerce_events';

class ProgramDetailsView extends Backbone.View {
  constructor(options) {
    const defaults = {
      el: '.js-program-details-wrapper',
      events: {
        'click .complete-program': 'trackPurchase',
      },
    };
    super(Object.assign({}, defaults, options));
  }

  initialize(options) {
    this.options = options;
    this.tpl = HtmlUtils.template(pageTpl);
    this.programModel = new Backbone.Model(this.options.programData);
    this.courseData = new Backbone.Model(this.options.courseData);
    this.certificateCollection = new Backbone.Collection(this.options.certificateData);
    this.completedCourseCollection = new CourseCardCollection(
      this.courseData.get('completed') || [],
      this.options.userPreferences,
    );
    this.inProgressCourseCollection = new CourseCardCollection(
      this.courseData.get('in_progress') || [],
      this.options.userPreferences,
    );
    this.remainingCourseCollection = new CourseCardCollection(
      this.courseData.get('not_started') || [],
      this.options.userPreferences,
    );

    this.render();

    const $courseUpsellButton = $('#program_dashboard_course_upsell_all_button');
    trackECommerceEvents.trackUpsellClick($courseUpsellButton, 'program_dashboard_program', {
      linkType: 'button',
      pageName: 'program_dashboard',
      linkCategory: 'green_upgrade',
    });
  }

  static getUrl(base, programData) {
    if (programData.uuid) {
      return `${base}&bundle=${encodeURIComponent(programData.uuid)}`;
    }
    return base;
  }

  render() {
    const completedCount = this.completedCourseCollection.length;
    const inProgressCount = this.inProgressCourseCollection.length;
    const remainingCount = this.remainingCourseCollection.length;
    const totalCount = completedCount + inProgressCount + remainingCount;
    const buyButtonUrl = ProgramDetailsView.getUrl(
      this.options.urls.buy_button_url,
      this.options.programData);
    let data = {
      totalCount,
      inProgressCount,
      remainingCount,
      completedCount,
      completeProgramURL: buyButtonUrl,
    };
    data = $.extend(data, this.programModel.toJSON());
    HtmlUtils.setHtml(this.$el, this.tpl(data));
    this.postRender();
  }

  postRender() {
    this.headerView = new HeaderView({
      model: new Backbone.Model(this.options),
    });

    if (this.remainingCourseCollection.length > 0) {
      new CollectionListView({
        el: '.js-course-list-remaining',
        childView: CourseCardView,
        collection: this.remainingCourseCollection,
        context: $.extend(this.options, { collectionCourseStatus: 'remaining' }),
      }).render();
    }

    if (this.completedCourseCollection.length > 0) {
      new CollectionListView({
        el: '.js-course-list-completed',
        childView: CourseCardView,
        collection: this.completedCourseCollection,
        context: $.extend(this.options, { collectionCourseStatus: 'completed' }),
      }).render();
    }

    if (this.inProgressCourseCollection.length > 0) {
      // This is last because the context is modified below
      new CollectionListView({
        el: '.js-course-list-in-progress',
        childView: CourseCardView,
        collection: this.inProgressCourseCollection,
        context: $.extend(this.options,
          { enrolled: gettext('Enrolled'), collectionCourseStatus: 'in_progress' },
        ),
      }).render();
    }

    this.sidebarView = new SidebarView({
      el: '.js-program-sidebar',
      model: this.programModel,
      courseModel: this.courseData,
      certificateCollection: this.certificateCollection,
      programRecordUrl: this.options.urls.program_record_url,
      industryPathways: this.options.industryPathways,
      creditPathways: this.options.creditPathways,
    });
  }

  trackPurchase() {
    const data = this.options.programData;
    window.analytics.track('edx.bi.user.dashboard.program.purchase', {
      category: `${data.variant} bundle`,
      label: data.title,
      uuid: data.uuid,
    });
  }
}

export default ProgramDetailsView;
