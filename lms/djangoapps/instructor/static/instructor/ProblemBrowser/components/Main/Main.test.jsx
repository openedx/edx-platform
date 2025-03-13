import { Provider } from 'react-redux';
import React from 'react';
import {
    render,
    screen,
    waitFor,
} from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import store from '../../data/store';
import Main from './Main';

jest.mock('BlockBrowser/components/BlockBrowser/BlockBrowserContainer', () => {
    function MockedBlockBrowserContainer() {
        return (
            <div data-testid="mocked-block-browser-container" className="block-browser">
                Mocked BlockBrowserContainer
            </div>
        );
    }
    return MockedBlockBrowserContainer;
});

describe('ProblemBrowser Main component', () => {
    const courseId = 'testcourse';
    const problemResponsesEndpoint = '/api/problem_responses/';
    const taskStatusEndpoint = '/api/task_status/';
    const excludedBlockTypes = [];
    const reportDownloadEndpoint = '/api/report_download';
    let fetchCourseBlocksMock;
    let createProblemResponsesReportTaskMock;
    let onSelectBlockMock;

    beforeEach(() => {
        fetchCourseBlocksMock = jest.fn();
        createProblemResponsesReportTaskMock = jest.fn();
        onSelectBlockMock = jest.fn();
    });

    const renderMainComponent = (props = {}) => (
        render(
            <Provider store={store}>
                <Main
                    courseId={courseId}
                    createProblemResponsesReportTask={createProblemResponsesReportTaskMock}
                    excludeBlockTypes={excludedBlockTypes}
                    fetchCourseBlocks={fetchCourseBlocksMock}
                    problemResponsesEndpoint={problemResponsesEndpoint}
                    onSelectBlock={onSelectBlockMock}
                    selectedBlock={props.selectedBlock}
                    taskStatusEndpoint={taskStatusEndpoint}
                    reportDownloadEndpoint={reportDownloadEndpoint}
                    ShowBtnUi="false"
                    {...props}
                />
            </Provider>,
        )
    );

    describe('Initial rendering', () => {
        test('should match snapshot with basic parameters', () => {
            const { container } = renderMainComponent();
            expect(container).toMatchSnapshot();
        });
        test('should match snapshot with selected block', () => {
            const { container } = renderMainComponent({ selectedBlock: 'some-selected-block' });
            expect(container).toMatchSnapshot();
        });
    });

    describe('Dropdown interactions', () => {
        test('should fetch course blocks when dropdown is toggled', async () => {
            renderMainComponent();
            await userEvent.click(screen.getByText('Select a section or problem'));
            await waitFor(() => {
                expect(fetchCourseBlocksMock).toHaveBeenCalledTimes(1);
                expect(fetchCourseBlocksMock).toHaveBeenCalledWith(courseId, excludedBlockTypes);
            });
        });

        test('should display dropdown when toggled', async () => {
            renderMainComponent();
            expect(screen.queryByTestId('mocked-block-browser-container')).toBeNull();
            await userEvent.click(screen.getByText('Select a section or problem'));
            await waitFor(() => expect(
                screen.getByTestId('mocked-block-browser-container'),
            ).toHaveClass('block-browser'));
            await userEvent.click(screen.getByText('Select a section or problem'));
            await waitFor(() => expect(screen.queryByTestId('mocked-block-browser-container')).toBeNull());
        });
    });
});
