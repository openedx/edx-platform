/* global gettext */

import PropTypes from 'prop-types';
import React from 'react';

class NoTextbooks extends React.Component {
  render() {
    return (this.props.TextbooksCollection.length === 0) && (
      <div className="no-textbook-content">
        <p>
          {gettext("You haven't added any textbooks to this course yet.")}
          <a href="#" className="button new-button">
            <span className="icon fa fa-plus" aria-hidden="true" />
            {gettext('Add your first textbook')}
          </a>
        </p>
      </div>
    );
  }
}

NoTextbooks.propTypes = {
  TextbooksCollection: PropTypes.shape().isRequired,
};

export default NoTextbooks;
