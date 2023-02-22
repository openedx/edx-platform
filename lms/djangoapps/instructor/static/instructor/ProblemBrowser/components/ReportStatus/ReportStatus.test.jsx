/* global test,describe,expect */
import React from 'react';
import renderer from 'react-test-renderer';
import ReportStatus from './ReportStatus';

describe('ReportStatus component', () => {
    test('render in progress status', () => {
        const component = renderer.create(
            <ReportStatus
                error={null}
                inProgress
                reportName={null}
                reportPath={null}
                succeeded={false}
            />,
        );
        const tree = component.toJSON();
        expect(tree).toMatchSnapshot();
    });

    test('render success status', () => {
        const component = renderer.create(
            <ReportStatus
                error={null}
                inProgress={false}
                reportName={'some-report-name'}
                reportPath={'/some/report/path.csv'}
                succeeded
            />,
        );
        const tree = component.toJSON();
        expect(tree).toMatchSnapshot();
    });

    test('render error status', () => {
        const component = renderer.create(
            <ReportStatus
                error={'some error status'}
                inProgress={false}
                reportName={null}
                reportPath={null}
                succeeded={false}
            />,
        );
        const tree = component.toJSON();
        expect(tree).toMatchSnapshot();
    });
});
