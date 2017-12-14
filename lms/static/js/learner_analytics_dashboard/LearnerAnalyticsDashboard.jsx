/* global gettext */

import PropTypes from 'prop-types';
import React from 'react';
import ReactDOM from 'react-dom';
import CircleChart from './CircleChart';
import CircleChartLegend from './CircleChartLegend';

export function LearnerAnalyticsDashboard(props) {
  console.log('props: ', props);
  const data = [
      {
        color: '#7ab',
        value: 0.15,
        label: 'Chucky'
      },
      {
        color: '#ebb90d',
        value: 0.25,
        label: 'Michael Myers'
      },
      {
        color: 'hotpink',
        value: 0.3,
        label: 'Freddy Krueger'
      },
      {
        color: '#73bde7',
        value: 0.3,
        label: 'Jason Vorhees'
      }
  ];

  return (
    <div className="analytics-group">
      <h2>Grading</h2>
      <h3>Weight</h3>
      <div className="grading-weight-wrapper">
        <CircleChart
          slices={data}
          centerHole={true}
          sliceBorder={{
              strokeColor: '#fff',
              strokeWidth: 1
          }}
        />
      </div>
      <CircleChartLegend data={data} />
    </div>
  );
}

