import React from 'react';
import classNames from 'classnames';
import PropTypes from 'prop-types';

class Discussions extends React.Component {
  constructor(props) {
    super(props);
  }

  getComparisons() {
    const experiments = window.experimentVariables || {};
    const {content_authored, profileImages} = this.props;
    const content_average = experiments.learnerAnalyticsDiscussionAverage || 4;
    let average_percent = 1;
    let authored_percent = 0;

    if (content_average > content_authored) {
      average_percent = 1;
      authored_percent = content_authored / content_average;
    } else {
      authored_percent = 1;
      average_percent = content_average / content_authored;
    }

    return (
      <div className="chart-wrapper">
        {this.getCountChart(content_authored, authored_percent, 'You', profileImages.medium)}
        {this.getCountChart(content_average, average_percent, 'Average graduate')}
      </div>
    );
  }

  getCountChart(count, percent, label, img = false) {
    var percentWidth;
    if (percent === 0) {
        percentWidth = '2px';
    } else {
      percentWidth = 'calc((100% - 40px) * ' + percent + ')';
    }
    return (
      <div className="count-chart">
        <div className={classNames(
                'chart-icon',
                {'fa fa-graduation-cap': !img}
              )}
              style={{backgroundImage: !!img ? `url(${img})` : 'none'}}
              aria-hidden="true"></div>
        <div className="chart-label">{label}</div>
        <div className="chart-display">
          <div className="chart-bar"
               aria-hidden="true"
               style={{width: `${percentWidth}`}}></div>
          <span className="user-count">{count}</span>
        </div>
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
