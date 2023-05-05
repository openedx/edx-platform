/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
import React from 'react';
import { Provider } from 'react-redux';
import BlockBrowserContainer from './components/BlockBrowser/BlockBrowserContainer';
import store from './data/store';

// eslint-disable-next-line react/function-component-definition
export const BlockBrowser = props => (
    <Provider store={store}>
        <BlockBrowserContainer {...props} />
    </Provider>
);

export default BlockBrowser;
