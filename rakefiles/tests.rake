
# Set up the clean and clobber tasks
CLOBBER.include(REPORT_DIR, 'test_root/*_repo', 'test_root/staticfiles')

$failed_tests = 0

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
    cmd = django_admin(system, :test, 'test', '--logging-clear-handlers', test_id)
    sh(run_under_coverage(cmd, system)) do |ok, res|
        if !ok and stop_on_failure
            abort "Test failed!"
        end
        $failed_tests += 1 unless ok
    end
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
    sh(django_admin(system, 'acceptance', 'harvest', '--debug-mode', '--tag -skip', harvest_args))
end


directory REPORT_DIR

task :clean_test_files do

    # Delete all files in the reports directory, while preserving
    # the directory structure.
    sh("find #{REPORT_DIR} -type f -print0 | xargs --no-run-if-empty -0 rm")

    # Reset the test fixtures
    sh("git clean -fqdx test_root")
end

TEST_TASK_DIRS = []

[:lms, :cms].each do |system|
    report_dir = report_dir_path(system)

    # Per System tasks
    desc "Run all django tests on our djangoapps for the #{system}"
    task "test_#{system}", [:test_id, :stop_on_failure] => ["clean_test_files", :predjango, "#{system}:gather_assets:test", "fasttest_#{system}"]

    # Have a way to run the tests without running collectstatic -- useful when debugging without
    # messing with static files.
    task "fasttest_#{system}", [:test_id, :stop_on_failure] => [report_dir, :install_prereqs, :predjango] do |t, args|
        args.with_defaults(:stop_on_failure => 'true', :test_id => nil)
        run_tests(system, report_dir, args.test_id, args.stop_on_failure)
    end

    # Run acceptance tests
    desc "Run acceptance tests"
    task "test_acceptance_#{system}", [:harvest_args] => ["#{system}:gather_assets:acceptance", "fasttest_acceptance_#{system}"]

    desc "Run acceptance tests without collectstatic"
    task "fasttest_acceptance_#{system}", [:harvest_args] => ["clean_test_files", :predjango, report_dir] do |t, args|
        args.with_defaults(:harvest_args => '')
        run_acceptance_tests(system, report_dir, args.harvest_args)
    end


    task :fasttest => "fasttest_#{system}"

    TEST_TASK_DIRS << system
end

Dir["common/lib/*"].select{|lib| File.directory?(lib)}.each do |lib|

    report_dir = report_dir_path(lib)

    desc "Run tests for common lib #{lib}"
    task "test_#{lib}"  => ["clean_test_files", report_dir] do
        ENV['NOSE_XUNIT_FILE'] = File.join(report_dir, "nosetests.xml")
        cmd = "nosetests #{lib}"
        sh(run_under_coverage(cmd, lib)) do |ok, res|
            $failed_tests += 1 unless ok
        end
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
end

task :test do
    TEST_TASK_DIRS.each do |dir|
        Rake::Task["test_#{dir}"].invoke(nil, false)
    end

    if $failed_tests > 0
        abort "Tests failed!"
    end
end

desc "Build the html, xml, and diff coverage reports"
task :coverage => :report_dirs do
    TEST_TASK_DIRS.each do |dir|
        report_dir = report_dir_path(dir)

        if !File.file?("#{report_dir}/.coverage")
            next
        end

        sh("coverage html --rcfile=#{dir}/.coveragerc")
        sh("coverage xml -o #{report_dir}/coverage.xml --rcfile=#{dir}/.coveragerc")
        sh("diff-cover #{report_dir}/coverage.xml --html-report #{report_dir}/diff_cover.html")
        sh("diff-cover #{report_dir}/coverage.xml")
        puts "\n\n"
    end
end
