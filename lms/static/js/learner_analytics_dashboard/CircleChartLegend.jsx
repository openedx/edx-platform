import React from 'react';
import classNames from 'classnames';
import PropTypes from 'prop-types';

class CircleChartLegend extends React.Component {
    // eslint-disable-next-line no-useless-constructor
    constructor(props) {
        super(props);
    }

    getList() {
        const {data} = this.props;

        return data.map(({value, label, sliceIndex}, index) => {
            const swatchClass = `swatch-${sliceIndex}`;
            return (
                // eslint-disable-next-line react/no-array-index-key
                <li className="legend-item" key={index}>
                    <div
                        className={classNames('color-swatch', swatchClass)}
                        aria-hidden="true"
                    />
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
    // eslint-disable-next-line react/forbid-prop-types
    data: PropTypes.array.isRequired
};

export default CircleChartLegend;
