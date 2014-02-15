JS_TEST_SUITES = {
    'lms' => 'lms/static/js_test.yml',
    'cms' => 'cms/static/js_test.yml',
    'cms-squire' => 'cms/static/js_test_squire.yml',
    'xmodule' => 'common/lib/xmodule/xmodule/js/js_test.yml',
    'common' => 'common/static/js_test.yml',
}

# Turn relative paths to absolute paths from the repo root.
JS_TEST_SUITES.each do |key, val|
    JS_TEST_SUITES[key] = File.join(REPO_ROOT, val)
end

# Define the directory for coverage reports
JS_REPORT_DIR = report_dir_path('javascript')
directory JS_REPORT_DIR

# Given an environment (a key in `JS_TEST_SUITES`)
# return the path to the JavaScript test suite description
# If `env` is nil, return a string containing
# all available descriptions.
def suite_for_env(env)
    if env.nil?
        return JS_TEST_SUITES.map{|key, val| val}.join(' ')
    else
        return JS_TEST_SUITES[env]
    end
end

# Run the tests using js-test-tool
# See js-test-tool docs for description of different
# command line arguments
def js_test_tool(env, command, do_coverage)
    suite = suite_for_env(env)
    xunit_report = File.join(JS_REPORT_DIR, 'javascript_xunit.xml')
    cmd = "js-test-tool #{command} #{suite} --use-firefox --timeout-sec 600 --xunit-report #{xunit_report}"

    if do_coverage
        report_dir = File.join(JS_REPORT_DIR, 'coverage.xml')
        cmd += " --coverage-xml #{report_dir}"
    end

    test_sh("javascript", cmd)
end

# Print a list of js_test commands for
# all available environments
def print_js_test_cmds(mode)
    JS_TEST_SUITES.each do |key, val|
        puts "    rake test:js:#{mode}[#{key}]"
    end
end

# Paver migration hack: because the CoffeeScript-specific asset command has been deprecated,
# we compile CoffeeScript ourselves
def compile_coffeescript()
    sh("node_modules/.bin/coffee --compile `find lms cms common -type f -name \"*.coffee\"`")
end

namespace :'test:js' do

    desc "Run the JavaScript tests and print results to the console"
    task :run, [:env] => [:clean_test_files, JS_REPORT_DIR] do |t, args|
        compile_coffeescript()

        if args[:env].nil?
            puts "Running all test suites.  To run a specific test suite, try:"
            print_js_test_cmds('run')
        end
        js_test_tool(args[:env], 'run', false)
    end

    desc "Run the JavaScript tests in your default browser"
    task :dev, [:env] => [:clean_test_files] do |t, args|
        compile_coffeescript()

        if args[:env].nil?
            puts "Error: No test suite specified.  Try one of these instead:"
            print_js_test_cmds('dev')
        else
            js_test_tool(args[:env], 'dev', false)
        end
    end

    desc "Run all JavaScript tests and collect coverage information"
    task :coverage => [:clean_reports_dir, :clean_test_files, JS_REPORT_DIR] do
        compile_coffeescript()
        js_test_tool(nil, 'run', true)
    end
end

# Default js_test is js_test:run
desc "Run all JavaScript tests and print results the the console"
task :'test:js' => :'test:js:run'

# Add the JS tests to the main test command
task :test => :'test:js:coverage'
