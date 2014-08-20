# -*- coding: utf-8 -*-
from lettuce import step, world
from nose.tools import assert_in, assert_true, assert_false


@step(u'Then I see a tables of modules progress')
def then_i_see_a_tables_of_modules_progress(step):
    world.wait_for_visible('.progress-report-list')

    if world.role == 'instructor':
        summary_text = "Test Course\nenrollments 1\nactive_students 1"
    elif world.role == 'staff':
        summary_text = "Test Course\nenrollments 2\nactive_students 2"

    modules_text = "i4x://edx/999/problem/Problem_1\ncorrect_map {u'i4x-org-cn-problem-unitid_2_1': 1}\ncount 2\ncourse_id edx/999/Test_Course\n"
    assert_true(world.browser.status_code.is_success())
    assert_in(summary_text, world.css_text("table.summary-table"))
    assert_in(modules_text, world.css_text("table.modules-table"))


@step(u'Then I generate CSV to mongodb')
def then_i_generate_csv_to_mongodb(step):
    world.wait_for_visible('.progress-report-list')
    world.css_click('input[name="generate-pgreport-csv"]')
    assert_true(world.browser.status_code.is_success())


@step(u'Then I download CSV from mongodb')
def then_i_download_csv_from_mongodb(step):
    world.wait_for_visible('.progress-report-list')
    world.css_click('input[name="download-pgreport-csv"]')
    assert_true(world.browser.status_code.is_success())
