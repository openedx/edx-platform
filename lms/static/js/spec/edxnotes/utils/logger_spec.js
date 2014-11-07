define(['js/edxnotes/utils/logger'],
    function(Logger) {
        'use strict';

        describe('Test logger', function() {
            var log, logs, logger;

            beforeEach(function() {
                logger = new Logger('id', 0); // 0 is silent mode
            });

            it('Tests if the logger keeps a correct history of logs', function() {
                logger.log('A log type', 'A first log');
                logger.log('A log type', 'A second log');

                logs = logger.getHistory();

                // Test first log
                log = logs[0];
                expect(log[0]).toBe('log');
                expect(log[1][0]).toBe('id');
                expect(log[1][1]).toBe('A log type');
                expect(log[1][2]).toBe('A first log');

                // Test second log
                log = logs[1];
                expect(log[0]).toBe('log');
                expect(log[1][0]).toBe('id');
                expect(log[1][1]).toBe('A log type');
                expect(log[1][2]).toBe('A second log');
            });

            it('Tests if the logger keeps a correct history of errors', function() {
                logger.error('An error type', 'A first error');
                logger.error('An error type', 'A second error');

                logs = logger.getHistory();

                // Test first error
                log = logs[0];
                expect(log[0]).toBe('error');
                expect(log[1][0]).toBe('id');
                expect(log[1][1]).toBe('An error type');
                expect(log[1][2]).toBe('A first error');

                // Test second error
                log = logs[1];
                expect(log[0]).toBe('error');
                expect(log[1][0]).toBe('id');
                expect(log[1][1]).toBe('An error type');
                expect(log[1][2]).toBe('A second error');
            });
        });
    }
);
