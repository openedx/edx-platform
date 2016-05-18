define(['jquery', 'coffee/src/instructor_dashboard/instructor_dashboard'],
    function($) {
        'use strict';
        
        describe("LMS Instructor Dashboard markup", function() {
            
            beforeEach(function() {
                loadFixtures('js/fixtures/instructor_dashboard/instructor_dashboard.html');
            });
            
            it("has proper markup for tab navigation widget", function() {
                expect($('.instructor-nav')).toHaveAttrs('role', 'tablist');
                expect($('.instructor-nav .nav-item')).toHaveAttrs({
                    'role': 'tab',
                    'aria-selected': 'false',
                    'aria-controls': true,
                    'tabindex': '-1'
                });
                expect($('.idash-section')).toHaveAttrs({
                    'role': 'tabpanel',
                    'aria-hidden': 'true',
                    'tabindex': '-1'
                });
            });
            
            describe("Ensures mouse functionality and correct ARIA", function() {
                var first_tab = $('.instructor-nav .nav-item')[0],
                    first_section = $(first_tab).data('section'),
                    second_tab = $('.instructor-nav .nav-item')[1],
                    second_section = $(second_tab).data('section');
                
                it("clicking a tab works as expected", function() {
                    $(first_tab).click();
                    $(second_tab).click();
                    
                    expect($(first_tab)).toHaveAttrs({
                        'aria-selected': 'true',
                        'tabindex': '-1'
                    });
                    
                    expect($(second_tab)).toHaveAttrs({
                        'aria-selected': 'false',
                        'tabindex': '0'
                    });
                    
                    expect($(first_section)).toHaveAttrs({
                        'tabindex': '-1',
                        'aria-hidden': 'true'
                    });
                    
                    expect($(second_section)).toHaveAttrs({
                        'tabindex': '0',
                        'aria-hidden': 'false'
                    });
                });
            });
            
            describe("Ensures keyboard functionality and correct ARIA", function() {
            
                it("has tabs that work with a keyboard", function() {
                    
                    // press right
                    // press down
                    // press up
                    // press left
                });
            });
            
            describe("Verifies location.hash sets and reads properly", function() {
                
                it("sets the location.hash", function() {
                    
                });
                
                it("reads the location.hash", function() {
                    
                });
            });
        });
    });
