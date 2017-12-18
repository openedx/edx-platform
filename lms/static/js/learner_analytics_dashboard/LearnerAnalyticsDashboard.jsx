/* global gettext */

import PropTypes from 'prop-types';
import React from 'react';
import ReactDOM from 'react-dom';
import CircleChart from './CircleChart';
import CircleChartLegend from './CircleChartLegend';
import Table from './Table';

export function LearnerAnalyticsDashboard(props) {
  console.log('props: ', props);
  const data = [
      {
        color: '#386F77',
        value: 0.15,
        label: 'Chucky'
      },
      {
        color: '#1ABC9C',
        value: 0.25,
        label: 'Michael Myers'
      },
      {
        color: '#92C9D3',
        value: 0.3,
        label: 'Freddy Krueger'
      },
      {
        color: '#73bde7',
        value: 0.3,
        label: 'Jason Vorhees'
      }
  ];

  const tableHeadings = ['Assessment', 'Passing', 'You'];
  const tableData = [
    {
      label: 'Problem Set 1',
      user: '12',
      passing: '20',
      total: '30'
    },
    {
      label: 'Problem Set 2',
      user: '20',
      passing: '10',
      total: '20'
    },
    {
      label: 'Problem Set 3',
      user: '0',
      passing: '40',
      total: '50'
    }
  ];

  return (
    <div className="learner-analytics-wrapper">
      <div className="analytics-group">
        <h2>Grading</h2>
        <h3>Weight</h3>
        <div className="grading-weight-wrapper">
          <div className="chart-wrapper">
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

        <h3>Graded Assessments</h3>
        <div className="graded-assessments-wrapper">
          <Table headings={tableHeadings} data={tableData} />
          <p class="footnote">*Calculated based on current average</p>
        </div>
      </div>
    </div>
  );
}

