import React from 'react';
import classNames from 'classnames';
import PropTypes from 'prop-types';

class CircleChartLegend extends React.Component {
  constructor(props) {
    super(props);
  }
  
  getList() {
    const {data} = this.props;

    return data.map(({ color, value, label }) => {
      const style = {
        backgroundColor: color
      }

      return (
        <li className="legend-item">
          <div className="color-swatch"
               style={style}
               aria-hidden="true"></div>
          <span className="label">{label}</span>
          <span className="percentage">{this.getPercentage(value)}</span>
        </li>
      );
    });
  }

  getPercentage(value) {
    const num = value * 100;

    return `${num}%`;
  }

  renderList() {
    return (
      <ul className="legend-list">
        {this.getList()}
      </ul>
    );
  }

  render() {
    return (
      <div className="legend">
        {this.renderList()}
      </div>
    );
  }
}


CircleChartLegend.propTypes = {
  data: PropTypes.array.isRequired
}

export default CircleChartLegend;
