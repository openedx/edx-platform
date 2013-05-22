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
    coffee_files = Dir["#{lib}/**/js/**/*.coffee", "common/static/coffee/src/**/*.coffee"]
    if !coffee_files.empty?
        sh("node_modules/.bin/coffee -c #{coffee_files.join(' ')}")
    end
    phantom_jasmine_path = File.expand_path("node_modules/phantom-jasmine")
    common_js_root = File.expand_path("common/static/js")
    common_coffee_root = File.expand_path("common/static/coffee/src")

    # Get arrays of spec and source files, ordered by how deep they are nested below the library
    # (and then alphabetically) and expanded from a relative to an absolute path
    spec_glob = File.join("#{lib}", "**", "spec", "**", "*.js")
    src_glob = File.join("#{lib}", "**", "src", "**", "*.js")
    js_specs = Dir[spec_glob].sort_by {|p| [p.split('/').length, p]} .map {|f| File.expand_path(f)}
    js_source = Dir[src_glob].sort_by {|p| [p.split('/').length, p]} .map {|f| File.expand_path(f)}

    template = ERB.new(File.read("#{lib}/jasmine_test_runner.html.erb"))
    template_output = "#{lib}/jasmine_test_runner.html"
    File.open(template_output, 'w') do |f|
        f.write(template.result(binding))
    end
    yield File.expand_path(template_output)
end

[:lms, :cms].each do |system|
    desc "Open jasmine tests for #{system} in your default browser"
    task "browse_jasmine_#{system}" => :assets do
        django_for_jasmine(system, true) do |jasmine_url|
            Launchy.open(jasmine_url)
            puts "Press ENTER to terminate".red
            $stdin.gets
        end
    end

    desc "Use phantomjs to run jasmine tests for #{system} from the console"
    task "phantomjs_jasmine_#{system}" => :assets do
        phantomjs = ENV['PHANTOMJS_PATH'] || 'phantomjs'
        django_for_jasmine(system, false) do |jasmine_url|
            sh("#{phantomjs} node_modules/phantom-jasmine/lib/run_jasmine_test.coffee #{jasmine_url}")
        end
    end
end

Dir["common/lib/*"].select{|lib| File.directory?(lib)}.each do |lib|
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
        phantomjs = ENV['PHANTOMJS_PATH'] || 'phantomjs'
        template_jasmine_runner(lib) do |f|
            sh("#{phantomjs} node_modules/phantom-jasmine/lib/run_jasmine_test.coffee #{f}")
        end
    end
end
