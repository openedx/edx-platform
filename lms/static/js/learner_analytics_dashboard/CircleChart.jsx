import React from 'react';
import classNames from 'classnames';
import PropTypes from 'prop-types';

const size = 100;
const radCircumference = Math.PI * 2;
const center = size / 2;
const radius = center - 1; // padding to prevent clipping

// Based on https://github.com/brigade/react-simple-pie-chart
class CircleChart extends React.Component {
  constructor(props) {
    super(props);
    this.getCenter = this.getCenter.bind(this);
    this.getSlices = this.getSlices.bind(this);
  }
  
  getCenter() {
    const {centerHole, sliceBorder} = this.props;
    if (centerHole) {
      const size = center / 2;
      return (
        <circle cx={center} cy={center} r={size} fill={sliceBorder.strokeColor} />
      );
    }
  }

  getSlices(slices, sliceBorder) {
    const total = slices.reduce((totalValue, { value }) => totalValue + value, 0);
    const {strokeColor, strokeWidth} = sliceBorder;

    let radSegment = 0;
    let lastX = radius;
    let lastY = 0;

    // Reverse a copy of the array so order start at 12 o'clock
    return slices.slice(0).reverse().map(({ value, sliceIndex }, index) => {
      // Should we just draw a circle?
      if (value === total) {
        return (
          <circle r={radius}
                  cx={center}
                  cy={center}
                  className="slice-1"
                  key={index} />
        );
      }

      if (value === 0) {
        return;
      }

      const valuePercentage = value / total;

      // Should the arc go the long way round?
      const longArc = (valuePercentage <= 0.5) ? 0 : 1;

      radSegment += valuePercentage * radCircumference;
      const nextX = Math.cos(radSegment) * radius;
      const nextY = Math.sin(radSegment) * radius;

      /**
       * d is a string that describes the path of the slice.
       * The weirdly placed minus signs [eg, (-(lastY))] are due to the fact
       * that our calculations are for a graph with positive Y values going up,
       * but on the screen positive Y values go down.
       */
      const d = [
        `M ${center},${center}`,
        `l ${lastX},${-lastY}`,
        `a${radius},${radius}`,
        '0',
        `${longArc},0`,
        `${nextX - lastX},${-(nextY - lastY)}`,
        'z',
      ].join(' ');

      lastX = nextX;
      lastY = nextY;

      return <path d={d}
                   className={`slice-${sliceIndex}`}
                   key={index}
                   stroke={strokeColor}
                   strokeWidth={strokeWidth} />;
    });
  }

  render() {
    const {slices, sliceBorder} = this.props;

    return (
      <svg viewBox={`0 0 ${size} ${size}`}>
        <g transform={`rotate(-90 ${center} ${center})`}>
          {this.getSlices(slices, sliceBorder)}
        </g>
        {this.getCenter()}
      </svg>
    );
  }
}

CircleChart.defaultProps = {
  sliceBorder: {
    strokeColor: '#fff',
    strokeWidth: 0
  }
};

CircleChart.propTypes = {
  slices: PropTypes.array.isRequired,
  centerHole: PropTypes.bool,
  sliceBorder: PropTypes.object
};

export default CircleChart;
