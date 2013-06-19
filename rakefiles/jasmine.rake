require 'colorize'
require 'erb'
require 'launchy'
require 'net/http'

PHANTOMJS_PATH = find_executable(ENV['PHANTOMJS_PATH'] || 'phantomjs')
PREFERRED_METHOD = PHANTOMJS_PATH.nil? ? 'browser' : 'phantomjs'
if PHANTOMJS_PATH.nil?
    puts("phantomjs not found on path. Set $PHANTOMJS_PATH. Using browser for jasmine tests".blue)
end

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
    phantom_jasmine_path = File.expand_path("node_modules/phantom-jasmine")
    jasmine_reporters_path = File.expand_path("node_modules/jasmine-reporters")
    common_js_root = File.expand_path("common/static/js")
    common_coffee_root = File.expand_path("common/static/coffee/src")

    # Get arrays of spec and source files, ordered by how deep they are nested below the library
    # (and then alphabetically) and expanded from a relative to an absolute path
    spec_glob = File.join(lib, "**", "spec", "**", "*.js")
    src_glob = File.join(lib, "**", "src", "**", "*.js")
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

def jasmine_browser(url, jitter=3, wait=10)
    # Jitter starting the browser so that the tests don't all try and
    # start the browser simultaneously
    sleep(rand(jitter))
    sh("python -m webbrowser -t '#{url}'")
    sleep(wait)
end

def jasmine_phantomjs(url)
    fail("phantomjs not found. Add it to your path, or set $PHANTOMJS_PATH") if PHANTOMJS_PATH.nil?
    test_sh("#{PHANTOMJS_PATH} node_modules/jasmine-reporters/test/phantomjs-testrunner.js #{url}")
end

# Wrapper tasks for the real browse_jasmine and phantomjs_jasmine
# tasks above. These have a nicer UI since there's no arg passing.
[:lms, :cms].each do |system|
    namespace :jasmine do
        namespace system do
            desc "Open jasmine tests for #{system} in your default browser"
            task :browser do
                Rake::Task[:assets].invoke(system, 'jasmine')
                django_for_jasmine(system, true) do |jasmine_url|
                    jasmine_browser(jasmine_url)
                end
            end

            desc "Open jasmine tests for #{system} in your default browser, and dynamically recompile coffeescript"
            task :'browser:watch' => :'assets:coffee:_watch' do
                django_for_jasmine(system, true) do |jasmine_url|
                    jasmine_browser(jasmine_url, jitter=0, wait=0)
                end
                puts "Press ENTER to terminate".red
                $stdin.gets
            end

            desc "Use phantomjs to run jasmine tests for #{system} from the console"
            task :phantomjs do
                Rake::Task[:assets].invoke(system, 'jasmine')
                phantomjs = ENV['PHANTOMJS_PATH'] || 'phantomjs'
                django_for_jasmine(system, false) do |jasmine_url|
                    jasmine_phantomjs(jasmine_url)
                end
            end
        end

        desc "Run jasmine tests for #{system} using #{PREFERRED_METHOD}"
        task system => "jasmine:#{system}:#{PREFERRED_METHOD}"

        task :phantomjs => "jasmine:#{system}:phantomjs"
        multitask :browser => "jasmine:#{system}:browser"
    end
end

static_js_dirs = Dir["common/lib/*"].select{|lib| File.directory?(lib)}
static_js_dirs << 'common/static/coffee'
static_js_dirs.select!{|lib| !Dir["#{lib}/**/spec"].empty?}

static_js_dirs.each do |dir|
    namespace :jasmine do
        namespace dir do
            desc "Open jasmine tests for #{dir} in your default browser"
            task :browser do
                # We need to use either CMS or LMS to preprocess files. Use LMS by default
                Rake::Task['assets:coffee'].invoke('lms', 'jasmine')
                template_jasmine_runner(dir) do |f|
                    jasmine_browser("file://#{f}")
                end
            end

            desc "Use phantomjs to run jasmine tests for #{dir} from the console"
            task :phantomjs do
                # We need to use either CMS or LMS to preprocess files. Use LMS by default
                Rake::Task[:assets].invoke('lms', 'jasmine')
                template_jasmine_runner(dir) do |f|
                    jasmine_phantomjs(f)
                end
            end
        end

        desc "Run jasmine tests for #{dir} using #{PREFERRED_METHOD}"
        task dir => "jasmine:#{dir}:#{PREFERRED_METHOD}"

        task :phantomjs => "jasmine:#{dir}:phantomjs"
        multitask :browser => "jasmine:#{dir}:browser"
    end
end

desc "Run all jasmine tests using #{PREFERRED_METHOD}"
task :jasmine => "jasmine:#{PREFERRED_METHOD}"

['phantomjs', 'browser'].each do |method|
    desc "Run all jasmine tests using #{method}"
    task "jasmine:#{method}"
end

task :test => :jasmine
