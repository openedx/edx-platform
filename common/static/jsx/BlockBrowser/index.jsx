import React from 'react';

import {Provider} from 'react-redux';
import store from './data/store';
import {BlockBrowserContainer} from "./components/BlockBrowser/BlockBrowserContainer";

export const BlockBrowser = props => (
    <Provider store={store}>
        <BlockBrowserContainer {...props} />
    </Provider>
);

export default BlockBrowser;
