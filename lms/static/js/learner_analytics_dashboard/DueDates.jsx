import React from 'react';
import classNames from 'classnames';
import PropTypes from 'prop-types';

const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

class DueDates extends React.Component {
  constructor(props) {
    super(props);
  }

  getDate(str) {
    const date = new Date(str);
    const day = days[date.getDay()];
    const month = months[date.getMonth()];
    const number = date.getDate();
    const year = date.getFullYear();

    return `${day} ${month} ${number}, ${year}`;
  }

  getLabel(type) {
    const {assignmentCounts} = this.props;
    if (assignmentCounts[type] < 2 ) {
      return type;
    } else {
      this.renderLabels[type] += 1;
      return type + ' ' + this.renderLabels[type];
    }
  }
  
  getList() {
    const {dates, assignmentCounts} = this.props;
    this.renderLabels = this.initLabelTracker(assignmentCounts);
 
    return dates.sort((a, b) => new Date(a.due) > new Date(b.due))
                .map(({ format, due }, index) => {
                  return (
                    <li className="date-item" key={index}>
                      <div className="label">{this.getLabel(format)}</div>
                      <div className="data">{this.getDate(due)}</div>
                    </li>
                  );
                });
  }

  initLabelTracker(list) {
    let labels = Object.keys(list);

    return labels.reduce((accumulator, key) => {
      accumulator[key] = 0;
      return accumulator;
    }, {}) 
  }

  renderList() {
    return (
      <ul className="date-list">
        {this.getList()}
      </ul>
    );
  }

  render() {
    return (
      <div className="due-dates">
        {this.renderList()}
      </div>
    );
  }
}


DueDates.propTypes = {
  dates: PropTypes.array.isRequired
}

export default DueDates;
