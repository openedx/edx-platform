import React from 'react';
import moment from 'moment';

//import { Table} from '@edx/paragon';
import { Button, Hyperlink, Table} from '@edx/paragon';

const entitlementColumns = [
  {
    label: 'User',
    key: 'user',
    columnSortable: true,
    onSort: () => {}
  },
  {
    label: 'Entitlement UUID',
    key: 'uuid',
    columnSortable: true,
    onSort: () => {},
  },
  {
    label: 'Course uuid',
    key: 'course_uuid',
    columnSortable: true,
    onSort: () => {},
  },
  {
    label: 'Enrollment',
    key: 'enrollment_course_run',
    columnSortable: true,
    onSort: () => {},
  },  
  {
	  label: 'Expired At',
	  key: 'expired_at',
	  columnSortable: true,
	  onSort: () => {},
  },  
  {
	  label: 'Created',
	  key: 'created',
	  columnSortable: true,
	  onSort: () => {},
  }, 
  {
	  label: 'Modified',
	  key: 'modified',
	  columnSortable: true,
	  onSort: () => {},
  }, 
  {
	  label: 'Mode',
	  key: 'mode',
	  columnSortable: true,
	  onSort: () => {},
  }, 
  {
	  label: 'Order',
	  key: 'order_number',
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

const reissueText = "Re-issue Entitlement";

class EntitlementTable extends React.Component{
	constructor(props){
		super(props)

    this.formattedEntitlementData = props.entitlements.map((entitlement, index)=>{
      return Object.assign({}, entitlement, {
        expired_at: entitlement.expired_at ? moment(entitlement.expired_at).format('MMM. D, YYYY') : '',
        created: moment(entitlement.created).format('MMM. D, YYYY'),
        modified: moment(entitlement.modified).format('MMM. D, YYYY'),
        order_number: <Hyperlink
          destination = {this.props.ecommerceUrl + entitlement.order_number + "/"} 
          content = {entitlement.order_number || ''}/>,
        button: <Button
          className = {['btn', 'btn-primary']}
          label = { reissueText }
          onClick = {this.handleReissueEntitlement.bind(this, entitlement)}/>
      })
    });
	}

  handleReissueEntitlement(entitlement){
    console.log('button click for entitlement', entitlement)
    this.props.openReissueModal(entitlement)
  }

	render(){

    const entitlementData = this.props.entitlements.map((entitlement, index)=>{
      return Object.assign({}, entitlement, {
        expired_at: entitlement.expired_at ? moment(entitlement.expired_at).format('MMM. D, YYYY') : '',
        created: moment(entitlement.created).format('MMM. D, YYYY'),
        modified: moment(entitlement.modified).format('MMM. D, YYYY'),
        order_number: <Hyperlink
          destination = {this.props.ecommerceUrl + entitlement.order_number + "/"} 
          content = {entitlement.order_number || ''}/>,
        button: <Button
          className = {['btn', 'btn-primary']}
          label = { reissueText }
          onClick = {this.handleReissueEntitlement.bind(this, entitlement)}/>
      })
    });

		return (
			<div>
	      <Table
	        data={entitlementData}
	        columns={entitlementColumns}
        />
	    </div>
	   )
	}
}

export default EntitlementTable;