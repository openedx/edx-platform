# Set up the clean and clobber tasks
CLOBBER.include(REPORT_DIR, 'test_root/*_repo', 'test_root/staticfiles')

# Create the directory to hold coverage reports, if it doesn't already exist.
directory REPORT_DIR

def test_id_dir(path)
    return File.join(".testids", path.to_s)
end

def run_under_coverage(cmd, root)
    cmd0, cmd_rest = cmd.split(" ", 2)
    # We use "python -m coverage" so that the proper python will run the importable coverage
    # rather than the coverage that OS path finds.
    cmd = "python -m coverage run --rcfile=#{root}/.coveragerc `which #{cmd0}` #{cmd_rest}"
    return cmd
end

def run_tests(system, report_dir, test_id=nil, stop_on_failure=true)

    # If no test id is provided, we need to limit the test runner
    # to the Djangoapps we want to test.  Otherwise, it will
    # run tests on all installed packages.

    default_test_id = "#{system}/djangoapps common/djangoapps"

    if system == :lms || system == :cms
        default_test_id += " #{system}/lib"
    end

    if test_id.nil?
        test_id = default_test_id

    # Handle "--failed" as a special case: we want to re-run only
    # the tests that failed within our Django apps
    elsif test_id == '--failed'
        test_id = "#{default_test_id} --failed"
    end

    cmd = django_admin(system, :test, 'test', test_id)
    test_sh(run_under_coverage(cmd, system))
end

# Run documentation tests
desc "Run documentation tests"
task :test_docs do
    # Be sure that sphinx can build docs w/o exceptions.
    test_message = "If test fails, you shoud run '%s' and look at whole output and fix exceptions.
(You shouldn't fix rst warnings and errors for this to pass, just get rid of exceptions.)"
    puts (test_message  % ["rake doc[docs,verbose]"]).colorize( :light_green )
    test_sh('rake builddocs')
end

task :clean_test_files do
    desc "Clean fixture files used by tests and .pyc files"
    sh("git clean -fqdx test_root/logs test_root/data test_root/staticfiles test_root/uploads")
    sh("find . -type f -name *.pyc -delete")
end

task :clean_reports_dir => REPORT_DIR do
    desc "Clean coverage files, to ensure that we don't use stale data to generate reports."

    # We delete the files but preserve the directory structure
    # so that coverage.py has a place to put the reports.
    sh("find #{REPORT_DIR} -type f -delete")
end

TEST_TASK_DIRS = []

[:lms, :cms].each do |system|
    report_dir = report_dir_path(system)
    test_id_dir = test_id_dir(system)

    directory test_id_dir

    # Per System tasks/
    desc "Run all django tests on our djangoapps for the #{system}"
    task "test_#{system}", [:test_id] => [
        :clean_test_files, :install_prereqs,
        "#{system}:gather_assets:test", "fasttest_#{system}"
    ]

    # Have a way to run the tests without running collectstatic -- useful when debugging without
    # messing with static files.
    task "fasttest_#{system}", [:test_id] => [test_id_dir, report_dir, :clean_reports_dir] do |t, args|
        args.with_defaults(:test_id => nil)
        run_tests(system, report_dir, args.test_id)
    end

    task :fasttest => "fasttest_#{system}"

    TEST_TASK_DIRS << system
end

Dir["common/lib/*"].select{|lib| File.directory?(lib)}.each do |lib|

    report_dir = report_dir_path(lib)
    test_id_dir = test_id_dir(lib)
    test_ids = File.join(test_id_dir(lib), '.noseids')

    directory test_id_dir

    desc "Run tests for common lib #{lib}"
    task "test_#{lib}", [:test_id] => [
        test_id_dir, report_dir, :clean_test_files,
        :clean_reports_dir, :install_prereqs
    ] do |t, args|
        args.with_defaults(:test_id => lib)
        ENV['NOSE_XUNIT_FILE'] = File.join(report_dir, "nosetests.xml")
        cmd = "nosetests --id-file=#{test_ids} #{args.test_id}"
        test_sh(run_under_coverage(cmd, lib))
    end
    TEST_TASK_DIRS << lib

    # There used to be a fasttest_#{lib} command that ran without coverage.
    # However, this is an inconsistent usage of "fast":
    # When running tests for lms and cms, "fast" means skipping
    # staticfiles collection, but still running under coverage.
    # We keep the fasttest_#{lib} command for backwards compatibility,
    # but make it an alias to the normal test command.
    task "fasttest_#{lib}" => "test_#{lib}"
end

task :report_dirs

TEST_TASK_DIRS.each do |dir|
    report_dir = report_dir_path(dir)
    directory report_dir
    task :report_dirs => [REPORT_DIR, report_dir]
    task 'test:python' => "test_#{dir}"
end

namespace :test do
    desc "Run all python tests"
    task :python, [:test_id]
end

desc "Run all tests"
task :test, [:test_id] => [:test_docs, 'test:python', 'i18n:test']

desc "Build the html, xml, and diff coverage reports"
task :coverage => :report_dirs do

    # Generate coverage for Python sources
    TEST_TASK_DIRS.each do |dir|
        report_dir = report_dir_path(dir)

        if File.file?("#{report_dir}/.coverage")

            # Generate the coverage.py HTML report
            sh("coverage html --rcfile=#{dir}/.coveragerc")

            # Generate the coverage.py XML report
            sh("coverage xml -o #{report_dir}/coverage.xml --rcfile=#{dir}/.coveragerc")

        end
    end

    # Find all coverage XML files (both Python and JavaScript)
    xml_reports = FileList[File.join(REPORT_DIR, '**/coverage.xml')]

    if xml_reports.length < 1
        puts "No coverage info found.  Run `rake test` before running `rake coverage`."
    else
        xml_report_str = xml_reports.join(' ')
        diff_html_path = report_dir_path('diff_coverage_combined.html')

        # Generate the diff coverage reports (HTML and console)
        sh("diff-cover #{xml_report_str} --html-report #{diff_html_path}")
        sh("diff-cover #{xml_report_str}")
        puts "\n"
    end
end
