import store from 'BlockBrowser/data/store';
import React from 'react';

import { Provider } from 'react-redux';

import CommunicatorContainer from './components/Communicator';

export const Communicator = props => (
  <Provider store={store}>
    <CommunicatorContainer {...props} />
  </Provider>
);
