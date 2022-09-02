/* global gettext */
import React from 'react';
import Cookies from 'js-cookie';

class RecommendationsPanel extends React.Component {
  constructor(props) {
    super(props);
    this.domainInfo = { domain: props.sharedCookieDomain, expires: 365, path: '/' };
    this.cookieName = props.cookieName;
    this.onCourseSelect = this.onCourseSelect.bind(this);
    this.getCourseList = this.getCourseList.bind(this);
    this.state = {
      isPersonalizedRecommendation: false,
      coursesList: [],
    };
  }

  onCourseSelect(courseKey) {
    window.analytics.track('edx.bi.user.recommended.course.click', {
      course_key: courseKey,
      is_personalized_recommendation: this.state.isPersonalizedRecommendation,
    });

    let recommendedCourses = Cookies.get(this.cookieName);
    if (typeof recommendedCourses === 'undefined') {
      recommendedCourses = { course_keys: [courseKey] };
    } else {
      recommendedCourses = JSON.parse(recommendedCourses);
      if (!recommendedCourses.course_keys.includes(courseKey)) {
        recommendedCourses.course_keys.push(courseKey);
      }
    }
    recommendedCourses['is_personalized_recommendation'] = this.state.isPersonalizedRecommendation;
    Cookies.set(this.cookieName, JSON.stringify(recommendedCourses), this.domainInfo);
  };

  getCourseList = async () => {
    const coursesRecommendationData = await fetch(`${this.props.lmsRootUrl}/api/dashboard/v0/recommendation/courses/`)
      .then(response => {
        if (response.status === 400) {
          return this.props.generalRecommendations;
        } else {
          if (window.hj) {
              window.hj('event', 'van_1046_show_recommendations_survey');
          }
          return response.json();

        }
      }).catch(() => {
        return this.props.generalRecommendations;
      });

    this.setState({
      coursesList: coursesRecommendationData.courses,
      isPersonalizedRecommendation: coursesRecommendationData.is_personalized_recommendation
    });
  };

  componentDidMount() {
    this.getCourseList();
  };


  render() {
    return (
      <div className="p-4 panel-background">
        <div className="recommend-heading mb-4">{gettext('Recommendations for you')}</div>
        <div className={this.state.coursesList.length ? '' : 'spinner-container'}>
          {this.state.coursesList.length ? this.state.coursesList.map(course => (
            <a href={course.marketing_url} className="course-link"
               onClick={() => this.onCourseSelect(course.course_key)}>
              <div className="course-card box-shadow-down-1 bg-white mb-3">
                <div className="box-shadow-down-1 image-box">
                  <img
                    className="panel-course-img"
                    src={course.logo_image_url}
                    alt="course image"
                  />
                </div>
                <div className="course-title pl-3">
                  {course.title}
                </div>
              </div>
            </a>
          )) : (
            <div className="d-flex justify-content-center align-items-center">
              <div role="status" className="spinner">
                <span className="sr-only">{gettext('loading')}</span>
              </div>
            </div>
          )}
        </div>

        {this.props.exploreCoursesUrl ? (
          <div className="d-flex justify-content-center">
            <a href={this.props.exploreCoursesUrl}
               className="panel-explore-courses justify-content-center align-items-center">
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
