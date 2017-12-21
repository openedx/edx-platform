/* global gettext */

import PropTypes from 'prop-types';
import React from 'react';
import ReactDOM from 'react-dom';
import CircleChart from './CircleChart';
import CircleChartLegend from './CircleChartLegend';
import GradeTable from './GradeTable';

export function LearnerAnalyticsDashboard(props) {
console.log('props: ', props);
  const {grading_policy, grades} = props;

  const gradeBreakdown = grading_policy.GRADER.map(({type, weight}, index) => {
    return {
      value: weight,
      label: type,
      sliceIndex: index + 1
    }
  }).sort((a, b) => a.value < b.value);

  const exGrades = [  
    {  
      "assignment_type":"Exam",
      "total_possible":6.0,
      "total_earned":3.0
    },
    {  
      "assignment_type":"Homework",
      "total_possible":5.0,
      "total_earned":4.0
    },
    {  
      "assignment_type":"Homework",
      "total_possible":11.0,
      "total_earned":0.0
    }
  ];

  // Get a list of assignment types minus duplicates
  const assignmentTypes = [...new Set(gradeBreakdown.map(value => value['label']))];

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
              slices={gradeBreakdown}
              centerHole={true}
              sliceBorder={{
                  strokeColor: '#fff',
                  strokeWidth: 1
              }}
            />
          </div>
          <CircleChartLegend data={gradeBreakdown} />
        </div>

        <h3>Graded Assessments</h3>
        <div className="graded-assessments-wrapper">
          <GradeTable assignmentTypes={assignmentTypes} data={exGrades} />
          <p className="footnote">*Calculated based on current average</p>
        </div>
      </div>
      <div className="discussions-group">
        <h2>Discussions</h2>
      </div>
      <div className="timing-group">
        <h2>Timing</h2>
      </div>
    </div>
  );
}

