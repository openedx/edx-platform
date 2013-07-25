# Set up the clean and clobber tasks
CLOBBER.include(REPORT_DIR, 'test_root/*_repo', 'test_root/staticfiles')

# Create the directory to hold coverage reports, if it doesn't already exist.
directory REPORT_DIR

def run_under_coverage(cmd, root)
    cmd0, cmd_rest = cmd.split(" ", 2)
    # We use "python -m coverage" so that the proper python will run the importable coverage
    # rather than the coverage that OS path finds.
    cmd = "python -m coverage run --rcfile=#{root}/.coveragerc `which #{cmd0}` #{cmd_rest}"
    return cmd
end

def run_tests(system, report_dir, test_id=nil, stop_on_failure=true)
    ENV['NOSE_XUNIT_FILE'] = File.join(report_dir, "nosetests.xml")
    dirs = Dir["common/djangoapps/*"] + Dir["#{system}/djangoapps/*"]
    test_id = dirs.join(' ') if test_id.nil? or test_id == ''
    cmd = django_admin(system, :test, 'test', '--logging-clear-handlers', '--liveserver=localhost:8000-9000', test_id)
    test_sh(run_under_coverage(cmd, system))
end

def run_acceptance_tests(system, report_dir, harvest_args)
    # HACK: Since now the CMS depends on the existence of some database tables
    # that used to be in LMS (Role/Permissions for Forums) we need to make
    # sure the acceptance tests create/migrate the database tables
    # that are represented in the LMS. We might be able to address this by moving
    # out the migrations from lms/django_comment_client, but then we'd have to
    # repair all the existing migrations from the upgrade tables in the DB.
    if system == :cms
        sh(django_admin('lms', 'acceptance', 'syncdb', '--noinput'))
        sh(django_admin('lms', 'acceptance', 'migrate', '--noinput'))
    end
    sh(django_admin(system, 'acceptance', 'syncdb', '--noinput'))
    sh(django_admin(system, 'acceptance', 'migrate', '--noinput'))
    test_sh(django_admin(system, 'acceptance', 'harvest', '--debug-mode', '--tag -skip', harvest_args))
end

# Run documentation tests
desc "Run documentation tests"
task :test_docs do
    # Be sure that sphinx can build docs w/o exceptions.
    test_message = "If test fails, you shoud run %s and look at whole output and fix exceptions.
(You shouldn't fix rst warnings and errors for this to pass, just get rid of exceptions.)"
    puts (test_message  % ["rake doc"]).colorize( :light_green )
    test_sh('rake builddocs')
    puts  (test_message  % ["rake doc[pub]"]).colorize( :light_green )
    test_sh('rake builddocs[pub]')
end

task :clean_test_files do
    desc "Clean fixture files used by tests"
    sh("git clean -fqdx test_root")
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

    # Per System tasks
    desc "Run all django tests on our djangoapps for the #{system}"
    task "test_#{system}", [:test_id] => [:clean_test_files, :predjango, "#{system}:gather_assets:test", "fasttest_#{system}"]

    # Have a way to run the tests without running collectstatic -- useful when debugging without
    # messing with static files.
    task "fasttest_#{system}", [:test_id] => [report_dir, :clean_reports_dir, :install_prereqs, :predjango] do |t, args|
        args.with_defaults(:test_id => nil)
        run_tests(system, report_dir, args.test_id)
    end

    # Run acceptance tests
    desc "Run acceptance tests"
    #gather_assets uses its own env because acceptance contains seeds to make the information unique
    #acceptance_static is acceptance without the random seeding
    task "test_acceptance_#{system}", [:harvest_args] => [:clean_test_files, "#{system}:gather_assets:acceptance_static", "fasttest_acceptance_#{system}"]

    desc "Run acceptance tests without collectstatic"
    task "fasttest_acceptance_#{system}", [:harvest_args] => [report_dir, :clean_reports_dir, :predjango] do |t, args|
        args.with_defaults(:harvest_args => '')
        run_acceptance_tests(system, report_dir, args.harvest_args)
    end


    task :fasttest => "fasttest_#{system}"

    TEST_TASK_DIRS << system
end

Dir["common/lib/*"].select{|lib| File.directory?(lib)}.each do |lib|

    report_dir = report_dir_path(lib)

    desc "Run tests for common lib #{lib}"
    task "test_#{lib}", [:test_id] => [report_dir, :clean_reports_dir] do |t, args|
        args.with_defaults(:test_id => lib)
        ENV['NOSE_XUNIT_FILE'] = File.join(report_dir, "nosetests.xml")
        cmd = "nosetests #{args.test_id}"
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
    task :test => "test_#{dir}"
end

desc "Run all tests"
task :test => :test_docs

desc "Build the html, xml, and diff coverage reports"
task :coverage => :report_dirs do

    found_coverage_info = false

    TEST_TASK_DIRS.each do |dir|
        report_dir = report_dir_path(dir)

        if !File.file?("#{report_dir}/.coverage")
            next
        else
            found_coverage_info = true
        end

        # Generate the coverage.py HTML report
        sh("coverage html --rcfile=#{dir}/.coveragerc")

        # Generate the coverage.py XML report
        sh("coverage xml -o #{report_dir}/coverage.xml --rcfile=#{dir}/.coveragerc")

        # Generate the diff coverage HTML report, based on the XML report
        sh("diff-cover #{report_dir}/coverage.xml --html-report #{report_dir}/diff_cover.html")

        # Print the diff coverage report to the console
        sh("diff-cover #{report_dir}/coverage.xml")
        puts "\n"
    end

    if not found_coverage_info
        puts "No coverage info found.  Run `rake test` before running `rake coverage`."
    end
end