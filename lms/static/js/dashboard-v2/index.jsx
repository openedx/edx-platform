import React from 'react';
import WrappedDashboardPage from '@arizzitano/graphql-dashboard/src/containers/WrappedDashboardPage';

export function DashboardV2({apiUri, username}) {
  return (
    <WrappedDashboardPage
      apiUri={apiUri}
      username={username}
    />
  );
};
