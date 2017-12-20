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
    "total_earned":4.0
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
  
  getTableGroup(type) {
    const {data} = this.props;
    const groupData = data.filter(value => {
      if (value['assignment_type'] === type) {
        return value;
      }
    });
    const multipleAssessments = groupData.length > 1;

    const rows = groupData.map(({assignment_type, total_possible, total_earned}, index) => {
      const label = multipleAssessments ? `${assignment_type} ${index + 1}` : assignment_type; 
      return (
        <tr key={index}>
          <td>{label}</td>
          <td>{total_possible}/{total_possible}</td>
          <td>{total_earned}/{total_possible}</td>
       </tr>
      );
    });

    return <tbody>{rows}</tbody>;
  }
  
  render() {
    const {assignmentTypes} = this.props;
    return (
      <table className="table">
        <thead className="table-head">
          <tr>
            <th>Assessment</th>
            <th>You</th>
            <th>Passing</th>
          </tr>
        </thead>
        {assignmentTypes.map(type => this.getTableGroup(type))}
       </table>
    )
  }
};

GradeTable.propTypes = {
  data: PropTypes.array.isRequired
}

export default GradeTable;
