# Run acceptance tests that use the bok-choy framework
# http://bok-choy.readthedocs.org/en/latest/
require 'dalli'


# Mongo databases that will be dropped before/after the tests run
BOK_CHOY_MONGO_DATABASE = "test"

# Control parallel test execution with environment variables
# Process timeout is the maximum amount of time to wait for results from a particular test case
BOK_CHOY_NUM_PARALLEL = ENV.fetch('NUM_PARALLEL', 1).to_i
BOK_CHOY_TEST_TIMEOUT = ENV.fetch("TEST_TIMEOUT", 300).to_f

# Ensure that we have a directory to put logs and reports
BOK_CHOY_DIR = File.join(REPO_ROOT, "common", "test", "acceptance")
BOK_CHOY_TEST_DIR = File.join(BOK_CHOY_DIR, "tests")
BOK_CHOY_LOG_DIR = File.join(REPO_ROOT, "test_root", "log")
directory BOK_CHOY_LOG_DIR

# Reports
BOK_CHOY_REPORT_DIR = report_dir_path("bok_choy")
BOK_CHOY_XUNIT_REPORT = File.join(BOK_CHOY_REPORT_DIR, "xunit.xml")
BOK_CHOY_COVERAGE_RC = File.join(BOK_CHOY_DIR, ".coveragerc")
directory BOK_CHOY_REPORT_DIR

# Directory that videos are served from
VIDEO_SOURCE_DIR = File.join(REPO_ROOT, "test_root", "data", "video")

BOK_CHOY_SERVERS = {
    :lms => { :port =>  8003, :log => File.join(BOK_CHOY_LOG_DIR, "bok_choy_lms.log") },
    :cms => { :port => 8031, :log => File.join(BOK_CHOY_LOG_DIR, "bok_choy_studio.log") }
}

BOK_CHOY_STUBS = {

    :xqueue => {
        :port => 8040,
        :log => File.join(BOK_CHOY_LOG_DIR, "bok_choy_xqueue.log"),
        :config => 'register_submission_url=http://0.0.0.0:8041/test/register_submission'
    },

    :ora => {
        :port => 8041,
        :log => File.join(BOK_CHOY_LOG_DIR, "bok_choy_ora.log"),
        :config => ''
    },

    :comments => {
        :port => 4567,
        :log => File.join(BOK_CHOY_LOG_DIR, "bok_choy_comments.log")
    },

    :video => {
        :port => 8777,
        :log => File.join(BOK_CHOY_LOG_DIR, "bok_choy_video_sources.log"),
        :config => "root_dir=#{VIDEO_SOURCE_DIR}"
    },

    :youtube => {
        :port => 9080,
        :log => File.join(BOK_CHOY_LOG_DIR, "bok_choy_youtube.log")
    }

}

# For the time being, stubs are used by both the bok-choy and lettuce acceptance tests
# For this reason, the stubs package is currently located in the Django app called "terrain"
# where other lettuce configuration is stored.
BOK_CHOY_STUB_DIR = File.join(REPO_ROOT, "common", "djangoapps", "terrain")

BOK_CHOY_CACHE = Dalli::Client.new('localhost:11211')


# Start the servers we will run tests on
def start_servers()
    BOK_CHOY_SERVERS.each do | service, info |
        address = "0.0.0.0:#{info[:port]}"
        cmd = "coverage run --rcfile=#{BOK_CHOY_COVERAGE_RC} -m manage #{service} --settings bok_choy runserver #{address} --traceback --noreload"
        singleton_process(cmd, logfile=info[:log])
    end

    BOK_CHOY_STUBS.each do | service, info |
        Dir.chdir(BOK_CHOY_STUB_DIR) do
            singleton_process(
                "python -m stubs.start #{service} #{info[:port]} #{info[:config]}",
                logfile=info[:log]
            )
        end
    end
end


# Wait until we get a successful response from the servers or time out
def wait_for_test_servers()
    BOK_CHOY_SERVERS.merge(BOK_CHOY_STUBS).each do | service, info |
        ready = wait_for_server("0.0.0.0", info[:port])
        if not ready
            fail("Could not contact #{service} test server")
        end
    end
end


def is_mongo_running()
    # The mongo command will connect to the service,
    # failing with a non-zero exit code if it cannot connect.
    output = `mongo --eval "print('running')"`
    return (output and output.include? "running")
end


def is_memcache_running()
    # We use a Ruby memcache client to attempt to set a key
    # in memcache.  If we cannot do so because the service is not
    # available, then this will raise an exception.
    BOK_CHOY_CACHE.set('test', 'test')
    return true
rescue Dalli::DalliError
    return false
end


def is_mysql_running()
    # We use the MySQL CLI client and capture its stderr
    # If the client cannot connect successfully, stderr will be non-empty
    output = `mysql -e "" 2>&1`
    return output == ""
end


# Run the bok choy tests
# `test_spec` is a nose-style test specifier relative to the test directory
# Examples:
# - path/to/test.py
# - path/to/test.py:TestFoo
# - path/to/test.py:TestFoo.test_bar
# It can also be left blank to run all tests in the suite.
def run_bok_choy(test_spec)

    # Default to running all tests if no specific test is specified
    if test_spec.nil?
        test_spec = BOK_CHOY_TEST_DIR
    else
        test_spec = File.join(BOK_CHOY_TEST_DIR, test_spec)
    end

    # Construct the nosetests command, specifying where to save screenshots and XUnit XML reports
    cmd = [
        "SCREENSHOT_DIR='#{BOK_CHOY_LOG_DIR}'", "nosetests", test_spec,
        "--with-xunit", "--xunit-file=#{BOK_CHOY_XUNIT_REPORT}", "--verbosity=2"
    ]

    # Configure parallel test execution, if specified
    if BOK_CHOY_NUM_PARALLEL > 1
        cmd += ["--processes=#{BOK_CHOY_NUM_PARALLEL}", "--process-timeout=#{BOK_CHOY_TEST_TIMEOUT}"]
    end

    # Run the nosetests command
    sh(cmd.join(" "))
end


def clear_mongo()
    sh("mongo #{BOK_CHOY_MONGO_DATABASE} --eval 'db.dropDatabase()' > /dev/null")
end


# Clean up data we created in the databases
def cleanup()
    sh(django_admin('lms', 'bok_choy', 'flush', '--noinput'))
    clear_mongo()
end


namespace :'test:bok_choy' do

    # Check that mongo is running
    task :check_mongo do
        if not is_mongo_running()
            fail("Mongo is not running locally.")
        end
    end

    # Check that memcache is running
    task :check_memcache do
        if not is_memcache_running()
            fail("Memcache is not running locally.")
        end
    end

    # Check that mysql is running
    task :check_mysql do
        if not is_mysql_running()
            fail("MySQL is not running locally.")
        end
    end

    # Check that all required services are running
    task :check_services => [:check_mongo, :check_memcache, :check_mysql]

    desc "Process assets and set up database for bok-choy tests"
    task :setup => [:check_mysql, :install_prereqs, BOK_CHOY_LOG_DIR] do

        # Reset the database
        sh("#{REPO_ROOT}/scripts/reset-test-db.sh")

        # Collect static assets
        sh("paver update_assets --settings=bok_choy")
    end

    desc "Run acceptance tests that use the bok-choy framework but skip setup"
    task :fast, [:test_spec] => [
        :check_services, BOK_CHOY_LOG_DIR, BOK_CHOY_REPORT_DIR, :clean_reports_dir
    ] do |t, args|

        # Clear any test data already in Mongo or MySQL and invalidate the cache
        clear_mongo()
        BOK_CHOY_CACHE.flush()
        sh(django_admin('lms', 'bok_choy', 'loaddata', 'common/test/db_fixtures/*.json'))

        # Ensure the test servers are available
        puts "Starting test servers...".green
        start_servers()
        puts "Waiting for servers to start...".green
        wait_for_test_servers()

        begin
            puts "Running test suite...".green
            run_bok_choy(args.test_spec)
        rescue
            puts "Tests failed!".red
            exit 1
        ensure
            puts "Cleaning up databases...".green
            cleanup()
        end
    end

    desc "Generate coverage reports for bok-choy tests"
    task :coverage => BOK_CHOY_REPORT_DIR do | t, args |
        puts "Combining coverage reports".red
        sh("coverage combine --rcfile=#{BOK_CHOY_COVERAGE_RC}")

        puts "Generating coverage reports".red
        sh("coverage html --rcfile=#{BOK_CHOY_COVERAGE_RC}")
        sh("coverage xml --rcfile=#{BOK_CHOY_COVERAGE_RC}")
        sh("coverage report --rcfile=#{BOK_CHOY_COVERAGE_RC}")
    end

end


# Default: set up and run the tests
desc "Run acceptance tests that use the bok-choy framework"
task :'test:bok_choy', [:test_spec] => [:'test:bok_choy:setup'] do |t, args|
    Rake::Task["test:bok_choy:fast"].invoke(args.test_spec)
end
