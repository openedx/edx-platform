import React from 'react';

import { Provider } from 'react-redux';
import store from './data/store';

import MainContainer from './components/Main/MainContainer.jsx';

// eslint-disable-next-line react/function-component-definition
export const EntitlementSupportPage = props => (
    <Provider store={store}>
        <MainContainer {...props} />
    </Provider>
);
