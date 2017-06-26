import React, {Component} from 'react';
import ReactDOM from 'react-dom';

class CourseOrLibraryListing extends React.Component {

    render() {
        let allowReruns = this.props.allowReruns,
            linkClass = this.props.linkClass;

        return (
            <ul className="list-courses">
                {
                    this.props.items.map((item, i) =>
                        <li key={i} className="course-item" data-course-key={item.course_key}>
                            <a className={linkClass} href={item.url}>
                                <h3 className="course-title" id={"title-"+linkClass+"-"+i}>{item.display_name}</h3>
                                <div className="course-metadata">
                                    <span className="course-org metadata-item">
                                        <span className="label">{gettext("Organization:")}</span> <span
                                        className="value">{item.org}</span>
                                    </span>
                                    <span className="course-num metadata-item">
                                        <span className="label">{gettext("Course Number:")}</span>
                                        <span className="value">{item.number}</span>
                                    </span>
                                    { item.run &&
                                        <span className="course-run metadata-item">
                                            <span className="label">{gettext("Course Run:")}</span>
                                            <span className="value">{item.run}</span>
                                        </span>
                                    }
                                    { item.can_edit === false &&
                                        <span className="extra-metadata">{gettext("(Read-only)")}</span>
                                    }
                                </div>
                            </a>
                            { item.lms_link && item.rerun_link &&
                                <ul className="item-actions course-actions">
                                    { allowReruns &&
                                    <li className="action action-rerun">
                                        <a href={item.rerun_link}
                                           className="button rerun-button"
                                           title={item.display_name}
                                           aria-describedby={"title-"+linkClass+"-"+i}
                                        >{gettext("Re-run Course")}</a>
                                    </li>
                                    }
                                    <li className="action action-view">
                                        <a href={item.lms_link} rel="external"
                                           className="button view-button"
                                           title={item.display_name}
                                           aria-describedby={"title-"+linkClass+"-"+i}
                                        >{gettext("View Live")}</a>
                                    </li>
                                </ul>
                            }
                        </li>
                    )
                }
            </ul>
        )
    }
}


export class StudioCourseIndex {
    constructor(selector, context, allowReruns) {
        ReactDOM.render(
            <CourseOrLibraryListing items={context} linkClass="course-link" allowReruns={allowReruns}/>,
            document.querySelector(selector)
        );
    }
}

export class StudioLibraryIndex {
    constructor(selector, context) {
        ReactDOM.render(
            <CourseOrLibraryListing items={context} linkClass="library-link" allowReruns={false}/>,
            document.querySelector(selector)
        );
    }
}
