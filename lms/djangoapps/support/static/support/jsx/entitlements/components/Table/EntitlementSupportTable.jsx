import React from 'react';
import moment from 'moment';
import PropTypes from 'prop-types';

import { Button, Hyperlink, DataTable } from '@edx/paragon';

const entitlementColumns = [
  {
    Header: 'User',
    accessor: 'user',
  },
  {
    Header: 'Course UUID',
    accessor: 'courseUuid',
  },
  {
    Header: 'Mode',
    accessor: 'mode',
  },
  {
    Header: 'Enrollment',
    accessor: 'enrollmentCourseRun',
  },
  {
    Header: 'Expired At',
    accessor: 'expiredAt',
  },
  {
    Header: 'Created',
    accessor: 'createdAt',
  },
  {
    Header: 'Modified',
    accessor: 'modifiedAt',
  },
  {
    Header: 'Order',
    accessor: 'orderNumber',
  },
  {
    Header: 'Actions',
    accessor: 'button',
    columnSortable: false,
    hideHeader: false,
  },
];

const parseEntitlementData = (entitlements, ecommerceUrl, openReissueForm) =>
  entitlements.map((entitlement) => {
    const { expiredAt, created, modified, orderNumber, enrollmentCourseRun } = entitlement;
    return Object.assign({}, entitlement, {
      expiredAt: expiredAt ? moment(expiredAt).format('lll') : '',
      createdAt: moment(created).format('lll'),
      modifiedAt: moment(modified).format('lll'),
      orderNumber: <Hyperlink
        destination={`${ecommerceUrl}${orderNumber}/`}
        content={orderNumber || ''}
      />,
      button: <Button
        disabled={!enrollmentCourseRun}
        className={['btn', 'btn-primary']}
        label="Reissue"
        onClick={() => openReissueForm(entitlement)}
      />,
    });
  });

const EntitlementSupportTable = props => (
  <DataTable
    data={parseEntitlementData(props.entitlements, props.ecommerceUrl, props.openReissueForm)}
    columns={entitlementColumns}
    itemCount={props.entitlements.length}
  />
);

EntitlementSupportTable.propTypes = {
  entitlements: PropTypes.arrayOf(PropTypes.shape({
    uuid: PropTypes.string.isRequired,
    courseUuid: PropTypes.string.isRequired,
    enrollmentCourseRun: PropTypes.string,
    created: PropTypes.string.isRequired,
    modified: PropTypes.string.isRequired,
    expiredAt: PropTypes.string,
    mode: PropTypes.string.isRequired,
    orderNumber: PropTypes.string,
    supportDetails: PropTypes.arrayOf(PropTypes.shape({
      supportUser: PropTypes.string,
      action: PropTypes.string,
      comments: PropTypes.string,
      unenrolledRun: PropTypes.string,
    })),
    user: PropTypes.string.isRequired,
  })).isRequired,
  ecommerceUrl: PropTypes.string.isRequired,
  openReissueForm: PropTypes.func.isRequired,
};

export default EntitlementSupportTable;
