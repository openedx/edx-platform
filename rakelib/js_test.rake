JS_TEST_SUITES = {
    'lms' => 'lms/static/js_test.yml',
    'cms' => 'cms/static/js_test.yml',
    'xmodule' => 'common/lib/xmodule/xmodule/js/js_test.yml',
    'common' => 'common/static/js_test.yml',
}

# Turn relative paths to absolute paths from the repo root.
JS_TEST_SUITES.each do |key, val|
    JS_TEST_SUITES[key] = File.join(REPO_ROOT, val)
end

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
    cmd = "js-test-tool #{command} #{suite} --use-firefox "

    if do_coverage
        report_dir = report_dir_path('js_coverage.xml')
        cmd += "--coverage-xml #{report_dir}"
    end

    sh(cmd)
end

# Print a list of js_test commands for
# all available environments
def print_js_test_cmds(mode)
    JS_TEST_SUITES.each do |key, val|
        puts "    rake js_test:#{mode}[#{key}]"
    end
end

namespace :js_test do

    desc "Run the JavaScript tests and print results to the console"
    task :run, [:env] => [:'assets:coffee'] do |t, args|
        if args[:env].nil?
            puts "Running all test suites.  To run a specific test suite, try:"
            print_js_test_cmds('run')
        end
        js_test_tool(args[:env], 'run', false)
    end

    desc "Run the JavaScript tests in your default browser"
    task :dev, [:env] => [:'assets:coffee'] do |t, args|
        if args[:env].nil?
            puts "Error: No test suite specified.  Try one of these instead:"
            print_js_test_cmds('dev')
        else
            js_test_tool(args[:env], 'dev', false)
        end
    end

    desc "Run all JavaScript tests and collect coverage information"
    task :coverage => [:'assets:coffee', REPORT_DIR] do
        js_test_tool(nil, 'run', true)
    end
end

# Add the JS tests to the main test command
task :test => :'js_test:coverage'
