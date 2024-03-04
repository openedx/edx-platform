/* global gettext */
/* eslint react/no-array-index-key: 0 */

import PropTypes from 'prop-types';
import React from 'react';

export function CourseOrLibraryListing(props) {
    const handleArchiveConfirmation = event => {
        event.preventDefault();
        var confirmation = confirm(gettext("Courses are archived by default when they pass their end date. Are you sure you want to archive this course anyway?"));
        if (confirmation) {
            window.location.href = event.target.getAttribute("href");
        }
    }

    const handleUnArchiveConfirmation = event => {
        event.preventDefault();
        var confirmation = confirm(gettext("Are you sure you want to unarchive this course? End date for this course will be changed to 1 year from now. This course will still have to be published."));
        if (confirmation) {
            window.location.href = event.target.getAttribute("href");
        }
    }
    const allowReruns = props.allowReruns;
    const linkClass = props.linkClass;
    const idBase = props.idBase;
    const items = props.items;
    const can_archive = props.can_archive;

    const sendTracking = () => {
        const url = props.tracking_api_url;
        const requestData = { event_data: { has_viewed_course: "true" } };
        fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(requestData),
        });
        clarity('set', 'has_viewed_course', 'true');
    };

    return (
        <div>
            <ul className="list-courses">
                {items.map((item, i) => (
                    <li
                        key={i}
                        className="course-item"
                        data-course-key={item.course_key}
                        onClick={props.default_course_id === item.course_key ? sendTracking : undefined}
                    >
                        <a className={linkClass} href={item.url}>
                            <h3 className="course-title" id={`title-${idBase}-${i}`}>
                                {item.display_name}
                            </h3>
                            <div className="course-metadata">
                                <span className="course-org metadata-item">
                                    <span className="label">{gettext("Organization:")}</span>
                                    <span className="value">{item.org}</span>
                                </span>
                                <span className="course-num metadata-item">
                                    <span className="label">{gettext("Course Number:")}</span>
                                    <span className="value">{item.number}</span>
                                </span>
                                {item.run && (
                                    <span className="course-run metadata-item">
                                        <span className="label">{gettext("Course Run:")}</span>
                                        <span className="value">{item.run}</span>
                                    </span>
                                )}
                                {item.can_edit === false && (
                                    <span className="extra-metadata">{gettext("(Read-only)")}</span>
                                )}
                            </div>
                        </a>
                        {item.lms_link && item.rerun_link && (
                            <ul className="item-actions course-actions">
                                {allowReruns && (
                                    <li className="action action-rerun">
                                        <a
                                            href={item.rerun_link}
                                            className="button rerun-button"
                                            aria-labelledby={`re-run-${idBase}-${i} title-${idBase}-${i}`}
                                            id={`re-run-${idBase}-${i}`}
                                        >
                                            {gettext("Re-run Course")}
                                        </a>
                                    </li>
                                )}
                                <li className="action action-view">
                                    <a
                                        href={item.lms_link}
                                        rel="external"
                                        className="button view-button"
                                        aria-labelledby={`view-live-${idBase}-${i} title-${idBase}-${i}`}
                                        id={`view-live-${idBase}-${i}`}
                                    >
                                        {gettext("View Live")}
                                    </a>
                                </li>
                                {can_archive && item.archive_link && (
                                    <li className="action action-view">
                                        <a
                                            href={item.archive_link}
                                            onClick={event => handleArchiveConfirmation(event)}
                                            className="button view-button"
                                            aria-labelledby={`view-archive-${idBase}-${i} title-${idBase}-${i}`}
                                            id={`view-archive-${idBase}-${i}`}
                                        >
                                            {gettext("Archive")}
                                        </a>
                                    </li>
                                )}
                                {can_archive && item.unarchive_link && (
                                    <li className="action action-view">
                                        <a
                                            href={item.unarchive_link}
                                            onClick={event => handleUnArchiveConfirmation(event)}
                                            className="button rerun-button"
                                            aria-labelledby={`view-unarchive-${idBase}-${i} title-${idBase}-${i}`}
                                            id={`view-unarchive-${idBase}-${i}`}
                                        >
                                            {gettext("Un-Archive")}
                                        </a>
                                    </li>
                                )}
                            </ul>
                        )}
                    </li>
                ))}
            </ul>
        </div>
    );
}

CourseOrLibraryListing.propTypes = {
  allowReruns: PropTypes.bool.isRequired,
  idBase: PropTypes.string.isRequired,
  items: PropTypes.arrayOf(PropTypes.object).isRequired,
  linkClass: PropTypes.string.isRequired,
  can_archive: PropTypes.bool.isRequired
};
