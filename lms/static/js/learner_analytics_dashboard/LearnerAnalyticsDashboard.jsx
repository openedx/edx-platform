/* eslint-disable-next-line no-unused-vars, no-redeclare */
/* global gettext */

// eslint-disable-next-line no-unused-vars
import PropTypes from 'prop-types';
import React from 'react';
// eslint-disable-next-line no-unused-vars
import ReactDOM from 'react-dom';
// eslint-disable-next-line no-unused-vars
import classNames from 'classnames';
// eslint-disable-next-line import/no-named-as-default, import/no-named-as-default-member
import CircleChart from './CircleChart';
import CircleChartLegend from './CircleChartLegend';
import GradeTable from './GradeTable';
// eslint-disable-next-line import/no-named-as-default, import/no-named-as-default-member, no-unused-vars
import DueDates from './DueDates';
import Discussions from './Discussions';

function arrayToObject(array) {
    return array.reduce((accumulator, obj) => {
        const key = Object.keys(obj)[0];
        accumulator[key] = obj[key];
        return accumulator;
    }, {});
}

function countByType(type, assignments) {
    let count = 0;
    // eslint-disable-next-line array-callback-return
    assignments.map(({format}) => {
        if (format === type) {
            count += 1;
        }
    });
    return count;
}

function getActiveUserString(count) {
    const users = (count === 1) ? 'User' : 'Users';
    return `${users} active in this course right now`;
}

function getAssignmentCounts(types, assignments) {
    const countsArray = types.map((type) => ({
        [type]: countByType(type, assignments)
    }));

    return arrayToObject(countsArray);
}

function getStreakIcons(count) {
    // eslint-disable-next-line prefer-spread
    return Array.apply(null, {length: count}).map((e, i) => (
        // eslint-disable-next-line react/no-array-index-key
        <span className="fa fa-trophy" aria-hidden="true" key={i} />
    ));
}

function getStreakEncouragement(count) {
    const action = (count > 0) ? 'Maintain' : 'Start';

    return `${action} your active streak by`;
}

function getStreakString(count) {
    const unit = (count === 1) ? 'week' : 'weeks';
    return (count > 0) ? `Active ${count} ${unit} in a row` : false;
}

// eslint-disable-next-line import/prefer-default-export
export function LearnerAnalyticsDashboard(props) {
    const {
        // eslint-disable-next-line camelcase
        grading_policy, grades, schedule, schedule_raw, week_streak, weekly_active_users, discussion_info, profile_images, passing_grade, percent_grade
    } = props;
    // eslint-disable-next-line camelcase
    const gradeBreakdown = grading_policy.GRADER.map(({type, weight}, index) => ({
        value: weight,
        label: type,
        sliceIndex: index + 1
    }));

    // Get a list of assignment types minus duplicates
    const assignments = gradeBreakdown.map(value => value.label);
    const assignmentTypes = [...new Set(assignments)];
    // eslint-disable-next-line no-unused-vars
    const assignmentCounts = getAssignmentCounts(assignmentTypes, schedule);

    // eslint-disable-next-line no-console
    console.log(schedule_raw);
    // eslint-disable-next-line no-console
    console.log(grades);

    return (
        <div className="learner-analytics-wrapper">
            <div className="main-block">
                <div className="analytics-group">
                    <h2 className="group-heading">Grading</h2>
                    {gradeBreakdown
            && <h3 className="section-heading">Weight</h3>}
                    {gradeBreakdown
            && (
                <div className="grading-weight-wrapper">
                    <div className="chart-wrapper">
                        <CircleChart
                            slices={gradeBreakdown}
                            centerHole
                            sliceBorder={{
                                strokeColor: '#f5f5f5',
                                strokeWidth: 2
                            }}
                        />
                    </div>
                    <CircleChartLegend data={gradeBreakdown} />
                </div>
            )}

                    <h3 className="section-heading">Graded Assignments</h3>
                    {/* TODO: LEARNER-3854: If implementing Learner Analytics, rename to graded-assignments-wrapper. */}
                    <div className="graded-assessments-wrapper">
                        <GradeTable
                            assignmentTypes={assignmentTypes}
                            grades={grades}
                            // eslint-disable-next-line camelcase
                            passingGrade={passing_grade}
                            // eslint-disable-next-line camelcase
                            percentGrade={percent_grade}
                        />
                        <div className="footnote">* Your current grade is calculated based on all assignments, including those you have not yet completed.</div>
                    </div>
                </div>
                <div className="analytics-group">
                    {/* eslint-disable-next-line camelcase */}
                    <Discussions {...discussion_info} profileImages={profile_images} />
                </div>
            </div>
            <div className="analytics-group sidebar week-streak">
                <h2 className="group-heading">Timing</h2>
                <div className="week-streak-wrapper">
                    <h3 className="section-heading">Week streak</h3>
                    {/* eslint-disable-next-line camelcase */}
                    {week_streak > 0
            && <div className="streak-icon-wrapper" aria-hidden="true">{getStreakIcons(week_streak)}</div>}
                    <p>{getStreakString(week_streak)}</p>
                    <p className="streak-encouragement">{getStreakEncouragement(week_streak)}</p>
                    <ul className="streak-criteria">
                        <li>Answering problems</li>
                        <li>Participating in discussions</li>
                        <li>Watching course videos</li>
                    </ul>
                </div>
                <div className="active-users-wrapper">
                    <span className="fa fa-user count-icon" aria-hidden="true" />
                    {/* eslint-disable-next-line camelcase */}
                    <span className="user-count">{weekly_active_users.toLocaleString('en', {useGrouping: true})}</span>
                    <p className="label">{getActiveUserString(weekly_active_users)}</p>
                </div>
            </div>
        </div>
    );
}
