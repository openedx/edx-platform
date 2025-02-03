// eslint-disable-next-line no-redeclare
/* global jest,test,describe,expect */
import { Provider } from 'react-redux';
import React from 'react';
import store from '../../data/store';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import Main from './Main';

describe('ProblemBrowser Main component', () => {
    const courseId = 'testcourse';
    const problemResponsesEndpoint = '/api/problem_responses/';
    const taskStatusEndpoint = '/api/task_status/';
    const excludedBlockTypes = [];
    const reportDownloadEndpoint = '/api/download_report/';

    test('render with basic parameters', () => {
        render(
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
                    reportDownloadEndpoint={reportDownloadEndpoint}
                    ShowBtnUi="false"
                />
            </Provider>
        );
        expect(screen.getByRole('button', { name: 'Select a section or problem' })).toBeInTheDocument();
    });
    

    test('render with selected block', () => {
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
                    reportDownloadEndpoint={reportDownloadEndpoint}
                    ShowBtnUi="false"
                />
            </Provider>
        );
        expect(screen.getByRole('button', { name: 'Select a section or problem' })).toBeInTheDocument();
    });

    test('fetch course block on toggling dropdown', async () => {
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
                    reportDownloadEndpoint={reportDownloadEndpoint}
                    ShowBtnUi="false"
                />
            </Provider>
        );
        const toggleButton = screen.getByRole('button', { name: 'Select a section or problem' });
        await userEvent.click(toggleButton);
        expect(fetchCourseBlocksMock).toHaveBeenCalledTimes(1);
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
                    reportDownloadEndpoint={reportDownloadEndpoint}
                    ShowBtnUi="false"
                />
            </Provider>
        );

        expect(screen.queryByText('Some expected block name')).toBeNull();
        const toggleButton = screen.getByRole("button", { name: 'Select a section or problem' });
        await userEvent.click(toggleButton);
        const blockName = screen.queryByText('Some expected block name');
        expect(blockName).toBeNull();
    });

    test('hide dropdown on second toggle', async () => {
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
                    reportDownloadEndpoint={reportDownloadEndpoint}
                    ShowBtnUi="false"
                />
            </Provider>
        );
        const toggleButton = screen.getByRole('button', { name: 'Select a section or problem' });

        await userEvent.click(toggleButton);
        await waitFor(() => {
            expect(screen.queryByText('Select a section or problem')).not.toBeNull();
        });
        await userEvent.click(toggleButton);
        await waitFor(() => {
            expect(screen.queryByText('Some expected block name')).toBeNull();
        });
    });
});
