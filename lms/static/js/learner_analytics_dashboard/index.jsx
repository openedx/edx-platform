/* global gettext */
/* eslint one-var: ["error", "always"] */
/* eslint no-alert: "error" */

import PropTypes from 'prop-types';
import React from 'react';
import ReactDOM from 'react-dom';


class RenderPage extends React.Component {
  constructor(props) {
    super(props);
  }

  render() {
    return (
      <div className="my-test-div">
        <h2>A React App!!!</h2>
      </div>
    );
  }
}

export class LearnerAnalyticsDashboard {
  constructor(context) {
    ReactDOM.render(
      <RenderPage context={context} />,
      document.getElementById('root'),
    );
  }
}
