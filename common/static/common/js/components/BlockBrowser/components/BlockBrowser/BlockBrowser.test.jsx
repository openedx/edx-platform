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
