/* global jest,test,describe,expect */
import { Button } from '@edx/paragon';
import BlockBrowserContainer from 'BlockBrowser/components/BlockBrowser/BlockBrowserContainer';
import { Provider } from 'react-redux';
import { shallow } from 'enzyme';
import React from 'react';
import renderer from 'react-test-renderer';
import store from '../../data/store';

import Main from './Main';

describe('ProblemBrowser Main component', () => {
    const courseId = 'testcourse';
    const problemResponsesEndpoint = '/api/problem_responses/';
    const taskStatusEndpoint = '/api/task_status/';
    const excludedBlockTypes = [];

    test('render with basic parameters', () => {
        const component = renderer.create(
            <Provider store={store}>
                <Main
                    courseId={courseId}
                    createProblemResponsesReportTask={jest.fn()}
                    excludeBlockTypes={excludedBlockTypes}
                    fetchCourseBlocks={jest.fn()}
                    problemResponsesEndpoint={problemResponsesEndpoint}
                    onSelectBlock={jest.fn()}
                    selectedBlock={null}
                    taskStatusEndpoint={taskStatusEndpoint}
                />
            </Provider>,
        );
        const tree = component.toJSON();
        expect(tree).toMatchSnapshot();
    });

    test('render with selected block', () => {
        const component = renderer.create(
            <Provider store={store}>
                <Main
                    courseId={courseId}
                    createProblemResponsesReportTask={jest.fn()}
                    excludeBlockTypes={excludedBlockTypes}
                    fetchCourseBlocks={jest.fn()}
                    problemResponsesEndpoint={problemResponsesEndpoint}
                    onSelectBlock={jest.fn()}
                    selectedBlock={'some-selected-block'}
                    taskStatusEndpoint={taskStatusEndpoint}
                />
            </Provider>,
        );
        const tree = component.toJSON();
        expect(tree).toMatchSnapshot();
    });

    test('fetch course block on toggling dropdown', () => {
        const fetchCourseBlocksMock = jest.fn();
        const component = renderer.create(
            <Provider store={store}>
                <Main
                    courseId={courseId}
                    createProblemResponsesReportTask={jest.fn()}
                    excludeBlockTypes={excludedBlockTypes}
                    fetchCourseBlocks={fetchCourseBlocksMock}
                    problemResponsesEndpoint={problemResponsesEndpoint}
                    onSelectBlock={jest.fn()}
                    selectedBlock={'some-selected-block'}
                    taskStatusEndpoint={taskStatusEndpoint}
                />
            </Provider>,
        );
        const instance = component.root.children[0].instance;
        instance.handleToggleDropdown();
        expect(fetchCourseBlocksMock.mock.calls.length).toBe(1);
    });

    test('display dropdown on toggling dropdown', () => {
        const component = shallow(
            <Main
                courseId={courseId}
                createProblemResponsesReportTask={jest.fn()}
                excludeBlockTypes={excludedBlockTypes}
                fetchCourseBlocks={jest.fn()}
                problemResponsesEndpoint={problemResponsesEndpoint}
                onSelectBlock={jest.fn()}
                selectedBlock={'some-selected-block'}
                taskStatusEndpoint={taskStatusEndpoint}
            />,
        );
        expect(component.find(BlockBrowserContainer).length).toBeFalsy();
        component.find(Button).find({ label: 'Select a section or problem' }).simulate('click');
        expect(component.find(BlockBrowserContainer).length).toBeTruthy();
    });
});
