/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
import React from 'react';
import { Provider } from 'react-redux';

import store from './data/store';
import MainContainer from './components/Main/MainContainer';

// eslint-disable-next-line react/function-component-definition
export const ProblemBrowser = props => (
    <Provider store={store}>
        <MainContainer {...props} />
    </Provider>
);
