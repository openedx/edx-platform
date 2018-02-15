import React from 'react';
import PropTypes from 'prop-types';

import { Table} from '@edx/paragon';
import { Button } from '@edx/paragon';
import { InputText } from '@edx/paragon';

const reissueText = "Re-issue Entitlement"

function action(){
  console.log('button click')
};


const entitlementData = [
  {
    user: 'Lil Bub',
    entitlement_uuid: '1863491287304',
    enrollment_run: 'Learnit',
    button: <Button
        className={['btn', 'btn-primary']}
        label= {reissueText}
        onClick={action('button-click')}/>
  },
];

const entitlementColumns = [
  {
    label: 'User',
    key: 'user',
    columnSortable: true,
    onSort: () => {}
  },
  {
    label: 'Entitlement',
    key: 'entitlement_uuid',
    columnSortable: true,
    onSort: () => {},
  },
  {
    label: 'Enrollment',
    key: 'enrollment_run',
    columnSortable: true,
    onSort: () => {},
  },  
  {
    label: 'Actions',
    key: 'button',
    columnSortable: false,
    hideHeader: false,
    onSort: () => {},
  },
];

function EntitlementSupportApp(props){
  return (
    <div>
      <div>
        <InputText
          name="search"
          label="Search"
          value="edx"
        />
        <Button
          label="Search"
          onClick={action('button-click')}
        />
        </div>
    <Table
      data={props.entitlement_data}
      columns={props.entitlement_columns}/>
    </div>
  )
}

function EntitlementSearchComponent (props){
  <div className="container">
    <div className="row">
      <div className="col-8">
        <InputText
          name="search"
          value="Username or email"
        />
      </div>
      <div className="col-4">
        <Button
          label="Search"
          className={['btn', 'btn-primary']}
          onClick={action('button-click')}
        />
      </div>
    </div>
  </div>
}

export class EntitlementSupportMainComponent extends React.Component{
  constructor(props){
    super(props)
  }

  render(){
    return (
      <div>
      <EntitlementSearchComponent/>
      <Table
        data={this.props.entitlement_data}
        columns={this.props.entitlement_columns}/>
      </div>
    )
  }
}


export class EntitlementSupportPage extends React.Component{
  render(){
    return <EntitlementSupportMainComponent entitlement_data={entitlementData} entitlement_columns={entitlementColumns}/>
  } 
}
