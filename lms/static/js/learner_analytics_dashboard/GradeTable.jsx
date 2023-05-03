import React from 'react';
import classNames from 'classnames';
import PropTypes from 'prop-types';
const exGrades = [  
    {  
        "assignment_type":"Exam",
        "total_possible":6.0,
        "total_earned":3.0
    },
    {  
        "assignment_type":"Homework",
        "total_possible":5.0,
    },
    {  
        "assignment_type":"Homework",
        "total_possible":11.0,
        "total_earned":0.0
    }
];

class GradeTable extends React.Component {
    constructor(props) {
        super(props);
    }
  
    getTableGroup(type, groupIndex) {
        const {grades} = this.props;
        const groupData = grades.filter(value => {
            if (value['assignment_type'] === type) {
                return value;
            }
        });
        const multipleAssignments = groupData.length > 1;

        const rows = groupData.map(({assignment_type, total_possible, total_earned, passing_grade}, index) => {
            const label = multipleAssignments ? `${assignment_type} ${index + 1}` : assignment_type; 
            return (
                <tr key={index}>
                    <td>{label}</td>
                    <td>{passing_grade}/{total_possible}</td>
                    <td>{total_earned}/{total_possible}</td>
                </tr>
            );
        });

        return rows.length ? <tbody className="type-group" key={groupIndex}>{rows}</tbody> : false;
    }
  
    render() {
        const {assignmentTypes, passingGrade, percentGrade} = this.props;
        return (
            <table className="table grade-table">
                <thead className="table-head">
                    <tr>
                        <th>Assignment</th>
                        <th>Passing</th>
                        <th>You</th>
                    </tr>
                </thead>
                {assignmentTypes.map((type, index) => this.getTableGroup(type, index))}
                <tfoot>
                    <tr className="totals">
                        <td className="footer-label">Total</td>
                        <td>{passingGrade}%</td>
                        <td>*{percentGrade}%</td>
                    </tr>
                </tfoot>
            </table>
        )
    }
};

GradeTable.propTypes = {
    assignmentTypes: PropTypes.array.isRequired,
    grades: PropTypes.array.isRequired,
    passingGrade: PropTypes.number.isRequired,
    percentGrade: PropTypes.number.isRequired
}

export default GradeTable;
