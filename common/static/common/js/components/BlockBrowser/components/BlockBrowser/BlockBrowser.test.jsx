/*
eslint-disable import/no-extraneous-dependencies, import/no-duplicates, import/order, import/no-self-import,
import/no-cycle, import/no-relative-packages, import/no-named-as-default, import/no-named-as-default-member,
import/named, import/no-useless-path-segments
*/
// eslint-disable-next-line no-redeclare
/* global jest,test,describe,expect */
import React from 'react';
import renderer from 'react-test-renderer';
import { BlockBrowser, BlockList } from './BlockBrowser';
import testBlockTree from './test-block-tree.json';

describe('BlockList component', () => {
    test('render with basic parameters', () => {
        const component = renderer.create(
            <BlockList
                blocks={testBlockTree.children}
                onSelectBlock={jest.fn()}
                selectedBlock={null}
                onChangeRoot={jest.fn()}
            />,
        );
        const tree = component.toJSON();
        expect(tree).toMatchSnapshot();
    });
});

describe('BlockBrowser component', () => {
    test('render with basic parameters', () => {
        const component = renderer.create(
            <BlockBrowser
                blocks={testBlockTree}
                onSelectBlock={jest.fn()}
                selectedBlock={null}
                onChangeRoot={jest.fn()}
            />,
        );
        const tree = component.toJSON();
        expect(tree).toMatchSnapshot();
    });

    test('render with custom classname', () => {
        const component = renderer.create(
            <BlockBrowser
                blocks={testBlockTree}
                className="some-class"
                onSelectBlock={jest.fn()}
                selectedBlock={null}
                onChangeRoot={jest.fn()}
            />,
        );
        const tree = component.toJSON();
        expect(tree).toMatchSnapshot();
    });
});
