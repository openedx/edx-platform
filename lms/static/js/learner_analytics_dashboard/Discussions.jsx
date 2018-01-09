import React from 'react';
import classNames from 'classnames';
import PropTypes from 'prop-types';

class Discussions extends React.Component {
  constructor(props) {
    super(props);
  }

  getComparisons() {
    const {content_authored} = this.props;
    const content_average = 7;
    let average_percent = 100;
    let authored_percent = 0;

    if (content_average > content_authored) {
      average_percent = 100;
      authored_percent = ( content_authored / content_average ) * 100;
    } else {
      authored_percent = 100;
      average_percent = ( content_average / content_authored ) * 100;
    }

    return (
      <div className="chart-wrapper">
        {this.getCountChart(content_authored, authored_percent + '%', 'You')}
        {this.getCountChart(content_average, average_percent + '%', 'Average graduate')}
      </div>
    );
  }

  testComparisons(content_authored, content_average) {
    let average_percent = 100;
    let authored_percent = 0;

    if (content_average > content_authored) {
      average_percent = 100;
      authored_percent = ( content_authored / content_average ) * 100;
    } else {
      authored_percent = 100;
      average_percent = ( content_average / content_authored ) * 100;
    }

    return (
      <div className="chart-wrapper">
        {this.getCountChart(content_authored, authored_percent + '%', 'You')}
        {this.getCountChart(content_average, average_percent + '%', 'Average graduate')}
      </div>
    );
  }

  getCountChart(count, percent, label) {
    return (
      <div className="count-chart">
        <span className="chart-icon" aria-hidden="true"></span>
        <div className="chart-label">{label}</div>
        <div className="chart-display">
          <div className="chart-bar"
               aria-hidden="true"
               style={{width: `calc(${percent})`}}></div>
        </div>
        <span className="count">{count}</span>
      </div>
    );
  }

  render() {
    const {content_authored, thread_votes} = this.props;

    return (
      <div className="discussions-wrapper">
        <h2 className="group-heading">Discussions</h2>
        <div className="comparison-charts">
          <h3 className="section-heading">Posts, comments, and replies</h3>
          {this.getComparisons()}
        </div>
        <div className="post-counts">
          <div className="votes-wrapper">
            <span className="fa fa-plus-square-o count-icon" aria-hidden="true"></span>
            <span className="user-count">{thread_votes}</span>
            <p className="label">Votes on your posts, comments, and replies</p>
          </div>
        </div>
      </div>
    );
  }
}


Discussions.propTypes = {
  content_authored: PropTypes.number.isRequired,
  thread_votes: PropTypes.number.isRequired
}

export default Discussions;
