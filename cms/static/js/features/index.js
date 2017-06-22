import React, {Component} from 'react';
import ReactDOM from 'react-dom';

class CourseListing extends React.Component {

    render() {
        let allowReruns = this.props.allowReruns;

        return (
            <ul className="list-courses">
                {
                    this.props.courses.map((course_info, i) =>
                        <li key={i} className="course-item" data-course-key={course_info.course_key}>
                            <a className="course-link" href={course_info.url}>
                                <h3 className="course-title">{course_info.display_name}</h3>
                                <div className="course-metadata">
                                    <span className="course-org metadata-item">
                                        <span className="label">Organization:</span> <span
                                        className="value">{course_info.org}</span>
                                    </span>
                                    <span className="course-num metadata-item">
                                        <span className="label">Course Number:</span>
                                        <span className="value">{course_info.number}</span>
                                    </span>
                                    <span className="course-run metadata-item">
                                        <span className="label">Course Run:</span> <span
                                        className="value">{course_info.run}</span>
                                    </span>
                                </div>
                            </a>

                            <ul className="item-actions course-actions">
                                { allowReruns &&
                                <li className="action action-rerun">
                                    <a href={course_info.rerun_link} className="button rerun-button">Re-run Course</a>
                                </li>
                                }
                                <li className="action action-view">
                                    <a href={course_info.lms_link} rel="external" className="button view-button">View Live</a>
                                </li>
                            </ul>
                        </li>
                    )
                }
            </ul>
        )
    }
}


export class StudioIndex {
    constructor(selector, context, allowReruns) {
        ReactDOM.render(
            <CourseListing courses={context} allowReruns={allowReruns}/>,
            document.querySelector(selector)
        );
    }
}