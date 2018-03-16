/* global gettext */

import PropTypes from 'prop-types';
import React from 'react';

class NoTextbooks extends React.Component {
  static handleClick() {
    window.models.TextbookCollection.add([{ editing: true }]);
  }

  constructor(props) {
    super(props);
    this.handleClick = NoTextbooks.handleClick.bind(this);
  }

  render() {
    return (this.props.TextbookCollection.length === 0) && (
      <div className="no-textbook-content">
        <p>
          {gettext("You haven't added any textbooks to this course yet.")}
          <button onClick={this.handleClick} className="button new-button">
            <span className="icon fa fa-plus" aria-hidden="true" />
            {gettext('Add your first textbook')}
          </button>
        </p>
      </div>
    );
  }
}

NoTextbooks.propTypes = {
  TextbookCollection: PropTypes.arrayOf(PropTypes.shape()).isRequired,
};

export default NoTextbooks;
