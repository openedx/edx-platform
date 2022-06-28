/* global gettext */
import React from 'react';

class RecommendationsPanel extends React.Component {
  constructor(props) {
    super(props);
    this.onCourseSelect = this.onCourseSelect.bind(this);
  }

  onCourseSelect(courseKey) {
    window.analytics.track('edx.bi.user.recommended.course.click', {
      course_key: courseKey,
      is_personalized_recommendation: false,  // TODO: Use state here with default false and update its value from API response.
    });
  };

  render() {
    return (
      <div className="p-4 panel-background">
        <div className="recommend-heading mb-4">{gettext('Recommendations for you')}</div>
        <div className="course-card box-shadow-down-1 bg-white mb-3">
          <div className="box-shadow-down-1 image-box">
            <img
              className="panel-course-img"
              src="https://source.unsplash.com/lQGJCMY5qcM"
              alt="course image"
            />
          </div>
          <div className="course-title pl-3">
            <a href="#" className="course-link" onClick={() => this.onCourseSelect('add-course-key-1')}>
                The Chemistry of Life
            </a>
          </div>
        </div>
        <div className="course-card box-shadow-down-1 bg-white mb-3">
          <div className="box-shadow-down-1 image-box">
            <img
              className="panel-course-img"
              src="https://source.unsplash.com/KltoLK6Mk-g"
              alt="course image"
            />
          </div>
          <div className="course-title pl-3">
            <a href="#" className="course-link" onClick={() => this.onCourseSelect('add-course-key-2')}>
                Drug Discovery & Medicinal Chemistry
            </a>
          </div>
        </div>
        <div className="course-card box-shadow-down-1 bg-white mb-3">
          <div className="box-shadow-down-1 image-box">
            <img
              className="panel-course-img"
              src="https://source.unsplash.com/_BJVJ4WcV1M"
              alt="course image"
            />
          </div>
          <div className="course-title pl-3">
            <a href="#" className="course-link" onClick={() => this.onCourseSelect('add-course-key-3')}>
                From Fossil Resources to Biomass: A Chemistry Perspective
            </a>
          </div>
        </div>
        <div className="course-card box-shadow-down-1 bg-white mb-3">
          <div className="box-shadow-down-1 image-box">
            <img
              className="panel-course-img"
              src="https://source.unsplash.com/NKhckz9B78c"
              alt="course image"
            />
          </div>
          <div className="course-title pl-3">
            <a href="#" className="course-link" onClick={() => this.onCourseSelect('add-course-key-4')}>
                Digital Biomaterials
            </a>
          </div>
        </div>
        <div className="course-card box-shadow-down-1 bg-white mb-3">
          <div className="box-shadow-down-1 image-box">
            <img
              className="panel-course-img"
              src="https://source.unsplash.com/x649mR6yBIs"
              alt="course image"
            />
          </div>
          <div className="course-title pl-3">
            <a href="#" className="course-link" onClick={() => this.onCourseSelect('add-course-key-5')}>
                Basic Steps in Magnetic Resonance
            </a>
          </div>
        </div>
        {this.props.exploreCoursesUrl ? (
          <div className="d-flex justify-content-center">
            <a href={this.props.exploreCoursesUrl} className="panel-explore-courses justify-content-center align-items-center">
              {gettext('Explore courses')}
              <span className="icon fa fa-search search-icon" aria-hidden="true"/>
            </a>
          </div>
        ) : null}
      </div>
    );
  }
}

export {RecommendationsPanel};
