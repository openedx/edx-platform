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
