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
      isLoading: true,
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
          return response.json();
        }
      }).catch(() => {
        return this.props.generalRecommendations;
      });

    if (window.hj && coursesRecommendationData.courses.length) {
      window.hj('event', 'van_1108_show_recommendations_survey');
    }

    this.setState({
      isLoading: false,
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
        {this.state.isLoading ? (
          <div>
            <div className="recommend-heading mb-4">{gettext('Recommendations for you')}</div>
            <div className="d-flex justify-content-center align-items-center spinner-container">
              <div role="status" className="spinner">
                <span className="sr-only">{gettext('loading')}</span>
              </div>
            </div>
          </div>
        ) : (
          <div>
            {this.state.coursesList.length ? (
              <div>
                <div className="recommend-heading mb-4">{gettext('Recommendations for you')}</div>
                <div>
                  {this.state.coursesList.map(course => (
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
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        )}
        {this.props.exploreCoursesUrl ? (
          <div>
            {!(this.state.coursesList.length || this.state.isLoading) &&
              <div className="recommend-heading mb-2 ml-2 mr-2">{gettext('Browse recently launched courses and see what\'s new in your favorite subjects.')}</div>}
            <div className="d-flex justify-content-center">
              <a href={this.props.exploreCoursesUrl}
                className="panel-explore-courses justify-content-center align-items-center">
                {gettext('Explore courses')}
                <span className="icon fa fa-search search-icon" aria-hidden="true"/>
              </a>
            </div>
          </div>
        ) : null}
      </div>
    );
  }
}

export {RecommendationsPanel};
