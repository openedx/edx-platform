/* global gettext */
import React from 'react';
import Cookies from 'js-cookie';

class RecommendationsPanel extends React.Component {
    constructor(props) {
        super(props);
        this.domainInfo = { domain: props.sharedCookieDomain, expires: 365, path: '/' };
        this.onCourseSelect = this.onCourseSelect.bind(this);
        this.getCourseList = this.getCourseList.bind(this);
        this.state = {
            isLoading: true,
            isControl: null,
            coursesList: [],
        };
    }

    onCourseSelect(courseKey, marketingUrl) {
        window.analytics.track('edx.bi.user.recommended.course.click', {
            course_key: courseKey,
            is_control: this.state.isControl,
            page: 'dashboard',
        });

        window.location.href = marketingUrl;
    };

    getCourseList = async () => {
        const coursesRecommendationData = await fetch(`${this.props.lmsRootUrl}/api/dashboard/v0/recommendation/courses/`)
            .then(response => response.json())
            .catch(() => ({
                courses: this.props.generalRecommendations,
            }));

        this.setState({
            coursesList: coursesRecommendationData.courses,
            isLoading: false,
            isControl: coursesRecommendationData.is_control === undefined ? null : coursesRecommendationData.is_control,
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
                                        <span
                                            role="link"
                                            className="course-link"
                                            onClick={() => this.onCourseSelect(course.course_key, course.marketing_url)}
                                        >
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
                                        </span>
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
