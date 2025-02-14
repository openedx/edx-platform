// eslint-disable-next-line no-redeclare
/* global jest,test,describe,expect */
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Provider } from 'react-redux';
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
                    ShowBtnUi="false"
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
                    selectedBlock="some-selected-block"
                    taskStatusEndpoint={taskStatusEndpoint}
                    ShowBtnUi="false"
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
                    selectedBlock="some-selected-block"
                    taskStatusEndpoint={taskStatusEndpoint}
                    ShowBtnUi="false"
                />
            </Provider>,
        );
        // eslint-disable-next-line prefer-destructuring
        const instance = component.root.children[0].instance;
        instance.handleToggleDropdown();
        expect(fetchCourseBlocksMock.mock.calls.length).toBe(1);
    });

    test('display dropdown on toggling dropdown', async () => {
        render(
            <Provider store={store}>
                <Main
                    courseId={courseId}
                    createProblemResponsesReportTask={jest.fn()}
                    excludeBlockTypes={excludedBlockTypes}
                    fetchCourseBlocks={jest.fn()}
                    problemResponsesEndpoint={problemResponsesEndpoint}
                    onSelectBlock={jest.fn()}
                    selectedBlock="some-selected-block"
                    taskStatusEndpoint={taskStatusEndpoint}
                    ShowBtnUi="false"
                />
            </Provider>,
        );
        expect(screen.queryByTestId('block-browser-container')).toBeNull();
        const toggleButton = screen.getByRole('button', { name: 'Select a section or problem' });
        await userEvent.click(toggleButton);
        await waitFor(() => {
            expect(screen.findByTestId('block-browser-container')).resolves.toBeInTheDocument();
        });
        await userEvent.click(toggleButton);
        await waitFor(() => {
            expect(screen.findByTestId('block-browser-container')).resolves.toBeInTheDocument();
        });
    });
});
