
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
    deprecated("jasmine:#{system}", "js_test:dev[#{system}]")
    deprecated("jasmine:#{system}:browser", "js_test:dev[#{system}]")
    deprecated("jasmine:#{system}:browser:watch", "js_test:dev[#{system}]")
    deprecated("jasmine:#{system}:phantomjs", "js_test:run[#{system}]")
    deprecated("#{system}:check_settings:jasmine", "")
    deprecated("#{system}:gather_assets:jasmine", "")
end

Dir["common/lib/*"].select{|lib| File.directory?(lib)}.each do |lib|
    deprecated("browse_jasmine_#{lib}", "jasmine:#{lib}:browser")
    deprecated("phantomjs_jasmine_#{lib}", "jasmine:#{lib}:phantomjs")
end

deprecated("browse_jasmine_discussion", "jasmine:common/static/coffee:browser")
deprecated("phantomjs_jasmine_discussion", "jasmine:common/static/coffee:phantomjs")
deprecated("jasmine:common/lib/xmodule", "js_test:run[xmodule]")
deprecated("jasmine:common/lib/xmodule:browser", "js_test:dev[xmodule]")
deprecated("jasmine:common/lib/xmodule:phantomjs", "js_test:run[xmodule]")
deprecated("jasmine:common/static/coffee", "js_test:run[common]")
deprecated("jasmine jasmine:common/static/coffee:browser", "js_test:dev[common]")
deprecated("jasmine:common/static/coffee:phantomjs", "js_test:run[common]")

deprecated("jasmine", "js_test:run")
deprecated("jasmine:phantomjs", "js_test:run")
deprecated("jasmine:browser", "js_test:dev")
