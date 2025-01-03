/* global jest, test, describe, expect */
import { Provider } from 'react-redux';
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';  // Importa render y fireEvent
import store from '../../data/store';

import Main from './Main';

describe('ProblemBrowser Main component', () => {
    const courseId = 'testcourse';
    const problemResponsesEndpoint = '/api/problem_responses/';
    const taskStatusEndpoint = '/api/task_status/';
    const excludedBlockTypes = [];

    test('render with basic parameters', () => {
        const { asFragment } = render(
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
            </Provider>
        );
        expect(asFragment()).toMatchSnapshot();
    });

    test('render with selected block', () => {
        const { asFragment } = render(
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
                />
            </Provider>
        );
        expect(asFragment()).toMatchSnapshot();
    });

    test('fetch course block on toggling dropdown', () => {
        const fetchCourseBlocksMock = jest.fn();
        render(
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
                />
            </Provider>
        );

        const toggleButton = screen.getByRole('button', { name: 'Select a section or problem' });
        fireEvent.click(toggleButton);
        expect(fetchCourseBlocksMock).toHaveBeenCalledTimes(1);
    });

    test('display dropdown on toggling dropdown', () => {
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
                />
            </Provider>
        );

        expect(screen.queryByTestId('block-browser-container')).toBeNull();
        const toggleButton = screen.getByRole('button', { name: 'Select a section or problem' });
        fireEvent.click(toggleButton);
        expect(screen.getByTestId('block-browser-container')).toBeInTheDocument();
    });
});
