/* global gettext */

import PropTypes from 'prop-types';
import React from 'react';

export class NoTextbooks extends React.Component {
  render() {
    return (
      <div className="no-textbook-content">
        <p>
          {gettext("You haven't added any textbooks to this course yet.")}
          <a href="#" className="button new-button">
            <span className="icon fa fa-plus" aria-hidden="true"></span>
            {gettext("Add your first textbook")}
          </a>
        </p>
      </div>
    );
  }
}

NoTextbooks.propTypes = {

};
