import React from 'react';
import classNames from 'classnames';
import PropTypes from 'prop-types';

class Table extends React.Component {
  constructor(props) {
    super(props);
    this.getTableHead = this.getTableHead.bind(this);
  }
  
  getTableBody() {
    const {data} = this.props;
    const rows = data.map(({label, user, passing, total}) => {
      return (
        <tr>
          <td>{label}</td>
          <td>{user}/{total}</td>
          <td>{passing}/{total}</td>
       </tr>
      );
    });

    return <tbody>{rows}</tbody>;
  }
  
  getTableHead() {
    const {headings} = this.props;
    const html = headings.map((title) => <th>{title}</th>);
    return (
      <thead className="table-head">
        <tr>
          {html} 
        </tr>
      </thead>
    );
  }
  
  render() {
    return (
      <table className="table">
        <colgroup>
          <col />
          <col span="2"/>
          <col />
        </colgroup>
        {this.getTableHead()}
        {this.getTableBody()}
       </table>
    )
  }
};

Table.propTypes = {
  headings: PropTypes.array.isRequired,
  data: PropTypes.array.isRequired
}

export default Table;
