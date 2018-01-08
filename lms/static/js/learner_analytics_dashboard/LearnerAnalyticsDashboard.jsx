/* global gettext */

import PropTypes from 'prop-types';
import React from 'react';
import ReactDOM from 'react-dom';
import CircleChart from './CircleChart';
import CircleChartLegend from './CircleChartLegend';
import GradeTable from './GradeTable';
import DueDates from './DueDates';

function arrayToObject(array) {
  return array.reduce((accumulator, obj) => {
    const key = Object.keys(obj)[0];
    accumulator[key] = obj[key];
    return accumulator;
  }, {})
}

function countByType(type, assignments) {
  let count = 0;
  assignments.map(({format}) => {
    if (format === type) {
      count += 1;
    }
  })
  return count;
}

function getActiveUserString(count) {
  const users = (count === 1) ? 'User' : 'Users';
  return `${users} active in this course right now`;
}

function getAssignmentCounts(types, assignments) {
  const countsArray = types.map((type) => {
    return {
      [type]: countByType(type, assignments)
    }
  });

  return arrayToObject(countsArray);
}

function getStreakIcons(count) {
  return Array.apply(null, { length: count }).map((e, i) => (
    <span className="fa fa-trophy" aria-hidden="true" key={i}></span>
  ));
}

function getStreakString(count) {
  const unit = (count ===1) ? 'week' : 'weeks';
  return `Logged in ${count} ${unit} in a row`;
}

export function LearnerAnalyticsDashboard(props) {
console.log('props: ', props);
  const {grading_policy, grades, schedule, week_streak, weekly_active_users} = props;
  // temp. for local dev
  // const week_streak = 3;
  // const weekly_active_users = 83400;
  const gradeBreakdown = grading_policy.GRADER.map(({type, weight}, index) => {
    return {
      value: weight,
      label: type,
      sliceIndex: index + 1
    }
  }); //.sort((a, b) => a.value < b.value);

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
  const assignments = gradeBreakdown.map(value => value['label']);
  const assignmentTypes = [...new Set(assignments)];
  const assignmentCounts = getAssignmentCounts(assignmentTypes, schedule);
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
      <div className="main-block">
        <div className="analytics-group">
          <h2 className="group-heading">Grading</h2>
          <h3 className="section-heading">Weight</h3>
          <div className="grading-weight-wrapper">
            <div className="chart-wrapper">
              <CircleChart
                slices={gradeBreakdown}
                centerHole={true}
                sliceBorder={{
                    strokeColor: '#f5f5f5',
                    strokeWidth: 2
                }}
              />
            </div>
            <CircleChartLegend data={gradeBreakdown} />
          </div>

          <h3 className="section-heading">Graded Assessments</h3>
          <div className="graded-assessments-wrapper">
            <GradeTable assignmentTypes={assignmentTypes} grades={grades} />
            <p className="footnote">*Calculated based on current average</p>
          </div>
          <CircleChartLegend data={gradeBreakdown} />
        </div>

        <h3>Graded Assessments</h3>
        <div className="graded-assessments-wrapper">
          <GradeTable assignmentTypes={assignmentTypes} data={exGrades} />
          <p className="footnote">*Calculated based on current average</p>
        </div>
      </div>
      <div className="analytics-group sidebar">
        <h2 className="group-heading">Timing</h2>
        <h3 className="section-heading">Course due dates</h3>
        <DueDates dates={schedule} assignmentCounts={assignmentCounts} />
        {week_streak > 0 && 
          <div className="week-streak-wrapper">
            <div className="streak-icon-wrapper" aria-hidden="true">{getStreakIcons(week_streak)}</div>
            <h3 className="section-heading">Week streak</h3>
            <p>{getStreakString(week_streak)}</p>
          </div>
        }
        <div className="active-users-wrapper">
          <span className="fa fa-user" aria-hidden="true"></span>
          <span className="user-count">{weekly_active_users.toLocaleString('en', {useGrouping:true})}</span>
          <p className="label">{getActiveUserString(weekly_active_users)}</p>
        </div>
      </div>
    </div>
  );
}

