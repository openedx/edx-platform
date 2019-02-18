/* global gettext */
/* eslint react/no-array-index-key: 0 */

import PropTypes from 'prop-types';
import React from 'react';
import ReactDOM from 'react-dom';

export class CourseOrLibraryListing extends React.Component {
  constructor(props) {
    super(props);
    this.allowReruns = props.allowReruns;
    this.linkClass = props.linkClass;
    this.idBase = props.idBase;
    this.state = {items: props.items, search: ""};
    this.searchHandler = this.searchHandler.bind(this);
  }

  searchHandler(e) {
    e.preventDefault();

    var searchString = e.target.value.toLowerCase();
    if (!searchString) {
      this.setState({items: this.props.items, search: e.target.value});
      return;
    }

    var filteredItems = this.props.items.filter(function(i) {
        var nameMatch = i.display_name.toLowerCase().includes(searchString);
        var keyMatch = (i.org + "/" + i.number + "/" + (i.run || "")).toLowerCase().includes(searchString);
        return nameMatch || keyMatch;
    });

    this.setState({items: filteredItems, search: e.target.value});
  }

  render() {
    return (
      <div>
        <input className="search" type="text" placeholder={gettext('Search')} onInput={this.searchHandler} value={this.state.search} />
        <ul className="list-courses">
          {
            this.state.items.map((item, i) =>
              (
                <li key={i} className="course-item" data-course-key={item.course_key}>
                  <a className={this.linkClass} href={item.url}>
                    <h3 className="course-title" id={`title-${this.idBase}-${i}`}>{item.display_name}</h3>
                    <div className="course-metadata">
                      <span className="course-org metadata-item">
                        <span className="label">{gettext('Organization:')}</span>
                        <span className="value">{item.org}</span>
                      </span>
                      <span className="course-num metadata-item">
                        <span className="label">{gettext('Course Number:')}</span>
                        <span className="value">{item.number}</span>
                      </span>
                      { item.run &&
                        <span className="course-run metadata-item">
                          <span className="label">{gettext('Course Run:')}</span>
                          <span className="value">{item.run}</span>
                        </span>
                      }
                      { item.can_edit === false &&
                        <span className="extra-metadata">{gettext('(Read-only)')}</span>
                      }
                    </div>
                  </a>
                  { item.lms_link && item.rerun_link &&
                    <ul className="item-actions course-actions">
                      { this.allowReruns &&
                        <li className="action action-rerun">
                          <a
                            href={item.rerun_link}
                            className="button rerun-button"
                            aria-labelledby={`re-run-${this.idBase}-${i} title-${this.idBase}-${i}`}
                            id={`re-run-${this.idBase}-${i}`}
                          >{gettext('Re-run Course')}</a>
                        </li>
                      }
                      <li className="action action-view">
                        <a
                          href={item.lms_link}
                          rel="external"
                          className="button view-button"
                          aria-labelledby={`view-live-${this.idBase}-${i} title-${this.idBase}-${i}`}
                          id={`view-live-${this.idBase}-${i}`}
                        >{gettext('View Live')}</a>
                      </li>
                    </ul>
                  }
                </li>
              ),
            )
          }
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
};
