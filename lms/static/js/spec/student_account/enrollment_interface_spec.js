define(['js/student_account/enrollment_interface'],
    function(EnrollmentInterface) {
        describe("edx.student.account.EnrollmentInterface", function() {
            'use strict';

            it('checks if a given course mode slug exists in an array of mode objects', function() {
                var courseModes = [ { slug: 'honor' }, { slug: 'professional' } ]

                expect( EnrollmentInterface.modeInArray( courseModes, 'professional' ) ).toBe(true);
                expect( EnrollmentInterface.modeInArray( courseModes, 'audit' ) ).toBe(false);
            });
        });
    }
);
