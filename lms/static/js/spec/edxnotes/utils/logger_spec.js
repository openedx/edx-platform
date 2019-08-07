define([
    'logger', 'js/edxnotes/utils/logger'
], function(Logger, NotesLogger) {
    'use strict';
    describe('Edxnotes NotesLogger', function() {
        var getLogger = function(id, mode) {
            return NotesLogger.getLogger(id, mode);
        };

        beforeEach(function() {
            spyOn(window.console, 'log');
            spyOn(window.console, 'error');
            spyOn(Logger, 'log');
        });

        it('keeps a correct history of logs', function() {
            var logger = getLogger('id', 1),
                logs, log;

            logger.log('A log type', 'A first log');
            logger.log('A log type', 'A second log');
            expect(window.console.log).toHaveBeenCalled();

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

        it('keeps a correct history of errors', function() {
            var logger = getLogger('id', 1),
                logs, log;
            logger.error('An error type', 'A first error');
            logger.error('An error type', 'A second error');
            expect(window.console.error).toHaveBeenCalled();

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

        it('can destroy the logger', function() {
            var logger = getLogger('id', 1),
                logs;

            logger.log('A log type', 'A first log');
            logger.error('An error type', 'A first error');
            logs = logger.getHistory();
            expect(logs.length).toBe(2);
            logger.destroy();
            logs = logger.getHistory();
            expect(logs.length).toBe(0);
        });

        it('do not store the history in silent mode', function() {
            var logger = getLogger('id', 0),
                logs;
            logger.log('A log type', 'A first log');
            logger.error('An error type', 'A first error');
            logs = logger.getHistory();
            expect(logs.length).toBe(0);
        });

        it('do not show logs in the console in silent mode', function() {
            var logger = getLogger('id', 0);
            logger.log('A log type', 'A first log');
            logger.error('An error type', 'A first error');
            expect(window.console.log).not.toHaveBeenCalled();
            expect(window.console.error).not.toHaveBeenCalled();
        });

        it('can use timers', function() {
            var logger = getLogger('id', 1),
                logs, log;

            spyOn(performance, 'now').and.returnValue(1);
            spyOn(Date, 'now').and.returnValue(1);
            logger.time('timer');
            performance.now.and.returnValue(201);
            Date.now.and.returnValue(201);
            logger.timeEnd('timer');

            logs = logger.getHistory();
            log = logs[0];
            expect(log[0]).toBe('log');
            expect(log[1][0]).toBe('id');
            expect(log[1][1]).toBe('timer');
            expect(log[1][2]).toBe(200);
            expect(log[1][3]).toBe('ms');
        });

        it('can emit an event properly', function() {
            var logger = getLogger('id', 0);
            logger.emit('event_name', {id: 'some_id'});
            expect(Logger.log).toHaveBeenCalledWith('event_name', {
                id: 'some_id'
            });
        });
    });
});
