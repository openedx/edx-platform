require 'colorize'
require 'erb'
require 'launchy'
require 'net/http'


def django_for_jasmine(system, django_reload)
    if !django_reload
        reload_arg = '--noreload'
    end

    port = 10000 + rand(40000)
    jasmine_url = "http://localhost:#{port}/_jasmine/"

    background_process(*django_admin(system, 'jasmine', 'runserver', '-v', '0', port.to_s, reload_arg).split(' '))

    up = false
    start_time = Time.now
    until up do
        if Time.now - start_time > 30
            abort "Timed out waiting for server to start to run jasmine tests"
        end
        begin
            response = Net::HTTP.get_response(URI(jasmine_url))
            puts response.code
            up = response.code == '200'
        rescue => e
            puts e.message
        ensure
            puts('Waiting server to start')
            sleep(0.5)
        end
    end
    yield jasmine_url
end

def template_jasmine_runner(lib)
    case lib
    when /common\/lib\/.+/
        coffee_files = Dir["#{lib}/**/js/**/*.coffee", "common/static/coffee/src/**/*.coffee"]
    when /common\/static\/coffee/
        coffee_files = Dir["#{lib}/**/*.coffee"]
    else
        puts('I do not know how to run jasmine tests for #{lib}')
        exit
    end
    if !coffee_files.empty?
        sh("node_modules/.bin/coffee -c #{coffee_files.join(' ')}")
    end
    phantom_jasmine_path = File.expand_path("node_modules/phantom-jasmine")
    jasmine_reporters_path = File.expand_path("node_modules/jasmine-reporters")
    common_js_root = File.expand_path("common/static/js")
    common_coffee_root = File.expand_path("common/static/coffee/src")

    # Get arrays of spec and source files, ordered by how deep they are nested below the library
    # (and then alphabetically) and expanded from a relative to an absolute path
    spec_glob = File.join("#{lib}", "**", "spec", "**", "*.js")
    src_glob = File.join("#{lib}", "**", "src", "**", "*.js")
    js_specs = Dir[spec_glob].sort_by {|p| [p.split('/').length, p]} .map {|f| File.expand_path(f)}
    js_source = Dir[src_glob].sort_by {|p| [p.split('/').length, p]} .map {|f| File.expand_path(f)}

    report_dir = report_dir_path("#{lib}/jasmine")
    template = ERB.new(File.read("common/templates/jasmine/jasmine_test_runner.html.erb"))
    template_output = "#{lib}/jasmine_test_runner.html"
    File.open(template_output, 'w') do |f|
        f.write(template.result(binding))
    end
    yield File.expand_path(template_output)
end

def run_phantom_js(url)
    phantomjs = ENV['PHANTOMJS_PATH'] || 'phantomjs'
    sh("#{phantomjs} node_modules/jasmine-reporters/test/phantomjs-testrunner.js #{url}")
end

# Open jasmine tests for :system in the default browser. The :env
# should (always?) be 'jasmine', but it's passed as an arg so that
# the :assets dependency gets it.
#
# This task should be invoked via the wrapper below, so we don't
# include a description to keep it from showing up in rake -T.
task :browse_jasmine, [:system, :env] => :assets do |t, args|
    django_for_jasmine(args.system, true) do |jasmine_url|
        Launchy.open(jasmine_url)
        puts "Press ENTER to terminate".red
        $stdin.gets
    end
end

# Use phantomjs to run jasmine tests from the console. The :env
# should (always?) be 'jasmine', but it's passed as an arg so that
# the :assets dependency gets it.
#
# This task should be invoked via the wrapper below, so we don't
# include a description to keep it from showing up in rake -T.
task :phantomjs_jasmine, [:system, :env] => :assets do |t, args|
    django_for_jasmine(args.system, false) do |jasmine_url|
        run_phantom_js(jasmine_url)
    end
end

# Wrapper tasks for the real browse_jasmine and phantomjs_jasmine
# tasks above. These have a nicer UI since there's no arg passing.
[:lms, :cms].each do |system|
    desc "Open jasmine tests for #{system} in your default browser"
    task "browse_jasmine_#{system}" do
        Rake::Task[:browse_jasmine].invoke(system, 'jasmine')
    end

    desc "Use phantomjs to run jasmine tests for #{system} from the console"
    task "phantomjs_jasmine_#{system}" do
        Rake::Task[:phantomjs_jasmine].invoke(system, 'jasmine')
    end
end

STATIC_JASMINE_TESTS = Dir["common/lib/*"].select{|lib| File.directory?(lib)}
STATIC_JASMINE_TESTS << 'common/static/coffee'

STATIC_JASMINE_TESTS.each do |lib|
    desc "Open jasmine tests for #{lib} in your default browser"
    task "browse_jasmine_#{lib}" do
        template_jasmine_runner(lib) do |f|
            sh("python -m webbrowser -t 'file://#{f}'")
            puts "Press ENTER to terminate".red
            $stdin.gets
        end
    end

    desc "Use phantomjs to run jasmine tests for #{lib} from the console"
    task "phantomjs_jasmine_#{lib}" do
        template_jasmine_runner(lib) do |f|
            run_phantom_js(f)
        end
    end
end

desc "Open jasmine tests for discussion in your default browser"
task "browse_jasmine_discussion" => "browse_jasmine_common/static/coffee"

desc "Use phantomjs to run jasmine tests for discussion from the console"
task "phantomjs_jasmine_discussion" => "phantomjs_jasmine_common/static/coffee"
