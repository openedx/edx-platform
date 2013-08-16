
require 'colorize'

def deprecated(deprecated, deprecated_by)
    task deprecated do
        puts("Task #{deprecated} has been deprecated. Use #{deprecated_by} instead. Waiting 5 seconds...".red)
        sleep(5)
        Rake::Task[deprecated_by].invoke
    end
end

[:lms, :cms].each do |system|
    deprecated("browse_jasmine_#{system}", "jasmine:#{system}:browser")
    deprecated("phantomjs_jasmine_#{system}", "jasmine:#{system}:phantomjs")
    deprecated("jasmine:#{system}", "test:js:dev[#{system}]")
    deprecated("jasmine:#{system}:browser", "test:js:dev[#{system}]")
    deprecated("jasmine:#{system}:browser:watch", "test:js:dev[#{system}]")
    deprecated("jasmine:#{system}:phantomjs", "test:js:run[#{system}]")
    deprecated("#{system}:check_settings:jasmine", "")
    deprecated("#{system}:gather_assets:jasmine", "")
end

Dir["common/lib/*"].select{|lib| File.directory?(lib)}.each do |lib|
    deprecated("browse_jasmine_#{lib}", "jasmine:#{lib}:browser")
    deprecated("phantomjs_jasmine_#{lib}", "jasmine:#{lib}:phantomjs")
end

deprecated("browse_jasmine_discussion", "jasmine:common/static/coffee:browser")
deprecated("phantomjs_jasmine_discussion", "jasmine:common/static/coffee:phantomjs")
deprecated("jasmine:common/lib/xmodule", "test:js:run[xmodule]")
deprecated("jasmine:common/lib/xmodule:browser", "test:js:dev[xmodule]")
deprecated("jasmine:common/lib/xmodule:phantomjs", "test:js:run[xmodule]")
deprecated("jasmine:common/static/coffee", "test:js:run[common]")
deprecated("jasmine jasmine:common/static/coffee:browser", "test:js:dev[common]")
deprecated("jasmine:common/static/coffee:phantomjs", "test:js:run[common]")

deprecated("jasmine", "test:js:run")
deprecated("jasmine:phantomjs", "test:js:run")
deprecated("jasmine:browser", "test:js:dev")
