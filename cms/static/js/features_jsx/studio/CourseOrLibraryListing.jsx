/* global gettext */
/* eslint react/no-array-index-key: 0 */

import PropTypes from 'prop-types';
import React from 'react';
import { Modal, Button } from '@edx/paragon/src';

export class CourseOrLibraryListing extends React.Component {
    constructor(props) {
        super(props);

        this.state = {
            isOpen: false,
            url: "",
            text: ""
        };
    }

    renderConfirmationDialog = () => {
        return (
            <div className="delete-confirmation-wrapper">
                <Modal
                    open={this.state.isOpen}
                    title={gettext("Are you sure?")}
                    aria-live="polite"
                    renderHeaderCloseButton={false}
                    onClose={() => this.setState({ isOpen: false })}
                    closeText={gettext("No")}
                    body={<p>{this.state.text}</p>}
                    buttons={[
                        <Button
                            label={gettext("Yes")}
                            display={gettext("Yes")}
                            buttonType="danger"
                            onClick={() => {
                                window.location.href = this.state.url;
                                this.setState({ isOpen: false });
                            }}
                        />
                    ]}
                />
            </div>
        );
    }

    handleArchiveConfirmation = event => {
        event.preventDefault();
        this.setState(
            {
                url: event.target.getAttribute("href"),
                text:
                    gettext("Courses are archived by default when they pass their end date. Are you sure \
        you want to archive this course anyway?")
            },
            () => {
                this.setState({ isOpen: true });
            }
        );
    }

    handleUnArchiveConfirmation = event => {
        event.preventDefault();
        this.setState(
            {
                url: event.target.getAttribute("href"),
                text:
                    gettext("Are you sure you want to unarchive this course? End date for this course will be \
        changed to 1 year from now. This course will still have to be published.")
            },
            () => {
                this.setState({ isOpen: true });
            }
        );
    }

    render() {
        const { allowReruns, linkClass, idBase, can_archive, items } = this.props;

        return (
            <div>
                {this.renderConfirmationDialog()}
                <ul className="list-courses">
                    {items.map((item, i) => (
                        <li key={i} className="course-item" data-course-key={item.course_key}>
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
                                                onClick={this.handleArchiveConfirmation}
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
                                                onClick={this.handleUnArchiveConfirmation}
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
}

CourseOrLibraryListing.propTypes = {
  allowReruns: PropTypes.bool.isRequired,
  idBase: PropTypes.string.isRequired,
  items: PropTypes.arrayOf(PropTypes.object).isRequired,
  linkClass: PropTypes.string.isRequired,
  can_archive: PropTypes.bool.isRequired
};
