define(['jquery', 'coffee/src/instructor_dashboard/instructor_dashboard'],
    function($) {
        'use strict';
        
        describe("LMS Instructor Dashboard", function() {
            var KEY = $.ui.keyCode,
            
            keyPressEvent = function(key) {
                return $.Event('keydown', { keyCode: key });
            };
            
            beforeEach(function() {
                loadFixtures('js/fixtures/instructor_dashboard/instructor_dashboard.html');
            });
            
            it("has proper markup for tablist", function() {
                expect($('.instructor-nav')).toHaveAttr('role', 'tablist');
            });
            
            it("has proper markup for tabs", function() {
                var tab_items = $('.instructor-nav .nav-item');
                
                $(tab_items).each(function(index, el) {
                    expect($(el)).toHaveAttr('role', 'tab');
                    expect($(el)).toHaveAttr('aria-selected', 'false');
                    expect($(el)).toHaveAttr('aria-controls');
                    expect($(el)).toHaveAttr('tabindex', '-1');
                });
            });
            
            it("has proper markup for tabpanels", function() {
                var tab_sections = $('.idash-section');
                
                $(tab_sections).each(function(index, el) {
                    expect($(el)).toHaveAttr('role', 'tabpanel');
                    expect($(el)).toHaveAttr('aria-hidden', 'true');
                    expect($(el)).toHaveAttr('tabindex', '-1');
                });
            });
            
            describe("ensures mouse functionality and proper ARIA", function() {
                
                it("by clicking a tab works as expected", function() {
                    var first_tab = $('.instructor-nav .nav-item')[0],
                        first_section = $(first_tab).data('section'),
                        second_tab = $('.instructor-nav .nav-item')[1],
                        second_section = $(second_tab).data('section');
                        
                    $(first_tab).click();
                    $(second_tab).click();
                    
                    console.log(first_tab, second_tab);
                    
                    expect($(first_tab)).toHaveAttr('aria-selected', 'false');
                    expect($(first_tab)).toHaveAttr('tabindex', '-1');
                    
                    expect($(second_tab)).toHaveAttr('aria-selected', 'true');
                    expect($(second_tab)).toHaveAttr('tabindex', '0');
                    
                    expect($(first_section)).toHaveAttr('aria-hidden', 'true');
                    expect($(first_section)).toHaveAttr('tabindex', '-1');
                    
                    expect($(second_section)).toHaveAttr('aria-hidden', 'false');
                    expect($(second_section)).toHaveAttr('tabindex', '0');
                });
            });
            
            describe("Ensures keyboard functionality and correct ARIA", function() {
                
                it("by pressing RIGHT and moving to the next tab", function() {
                    var first_tab = $('.instructor-nav .nav-item')[0],
                        first_section = $(first_tab).data('section'),
                        second_tab = $('.instructor-nav .nav-item')[1],
                        second_section = $(second_tab).data('section');

                    first_tab.focus();
                    first_tab.trigger(keyPressEvent(KEY.RIGHT));
                    
                    expect(first_tab).toHaveAttr('aria-selected', 'false');
                    expect(first_tab).toHaveAttr('tabindex', '-1');
                    
                    expect(second_tab).toHaveAttr('aria-selected', 'true');
                    expect(second_tab).toHaveAttr('tabindex', '0');
                    
                    expect(first_section).toHaveAttr('aria-hidden', 'true');
                    expect(first_section).toHaveAttr('tabindex', '-1');
                    
                    expect(second_section).toHaveAttr('aria-hidden', 'false');
                    expect(second_section).toHaveAttr('tabindex', '0');
                });
                
                it("by pressing DOWN and moving to the next tab", function() {
                    var second_tab = $('.instructor-nav .nav-item')[1],
                        second_section = $(second_tab).data('section'),
                        third_tab = $('.instructor-nav .nav-item')[2],
                        third_section = $(second_tab).data('section');
                        
                    second_tab.focus();
                    second_tab.trigger(keyPressEvent(KEY.DOWN));
                    
                    expect(second_tab).toHaveAttr('aria-selected', 'false');
                    expect(second_tab).toHaveAttr('tabindex', '-1');
                    
                    expect(third_tab).toHaveAttr('aria-selected', 'true');
                    expect(third_tab).toHaveAttr('tabindex', '0');
                    
                    expect(second_section).toHaveAttr('aria-hidden', 'true');
                    expect(second_section).toHaveAttr('tabindex', '-1');
                    
                    expect(third_section).toHaveAttr('aria-hidden', 'false');
                    expect(third_section).toHaveAttr('tabindex', '0');
                });
                
                it("by pressing LEFT and moving to the previous tab", function() {
                    var second_tab = $('.instructor-nav .nav-item')[1],
                        second_section = $(second_tab).data('section'),
                        third_tab = $('.instructor-nav .nav-item')[2],
                        third_section = $(second_tab).data('section');

                    third_tab.focus();
                    third_tab.trigger(keyPressEvent(KEY.LEFT));
                    
                    expect(second_tab).toHaveAttr('aria-selected', 'true');
                    expect(second_tab).toHaveAttr('tabindex', '0');
                    
                    expect(third_tab).toHaveAttr('aria-selected', 'false');
                    expect(third_tab).toHaveAttr('tabindex', '-1');
                    
                    expect(second_section).toHaveAttr('aria-hidden', 'false');
                    expect(second_section).toHaveAttr('tabindex', '0');
                    
                    expect(third_section).toHaveAttr('aria-hidden', 'true');
                    expect(third_section).toHaveAttr('tabindex', '-1');
                });
                
                it("by pressing UP and moving to the previous tab", function() {
                    var first_tab = $('.instructor-nav .nav-item')[0],
                        first_section = $(first_tab).data('section'),
                        second_tab = $('.instructor-nav .nav-item')[1],
                        second_section = $(second_tab).data('section');

                    second_tab.focus();
                    second_tab.trigger(keyPressEvent(KEY.UP));
                    
                    expect(first_tab).toHaveAttr('aria-selected', 'true');
                    expect(first_tab).toHaveAttr('tabindex', '0');
                    
                    expect(second_tab).toHaveAttr('aria-selected', 'false');
                    expect(second_tab).toHaveAttr('tabindex', '-1');
                    
                    expect(first_section).toHaveAttr('aria-hidden', 'false');
                    expect(first_section).toHaveAttr('tabindex', '0');
                    
                    expect(second_section).toHaveAttr('aria-hidden', 'true');
                    expect(second_section).toHaveAttr('tabindex', '-1');
                });
            });
            
            describe("Verifies location.hash sets and reads properly", function() {
                
                it("by setting the location.hash", function() {
                    
                });
                
                it("by reading the location.hash", function() {
                    
                });
            });
        });
    });
