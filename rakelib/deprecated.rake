
require 'colorize'

def deprecated(deprecated, deprecated_by, *args)
    task deprecated do
        if args.length > 0 then
            args_str = args.join(',')
            new_cmd = "#{deprecated_by}[#{args_str}]"
        else
            new_cmd = deprecated_by
        end
        puts("Task #{deprecated} has been deprecated. Use #{new_cmd} instead. Waiting 5 seconds...".red)
        sleep(5)
        Rake::Task[deprecated_by].invoke(*args)
    end
end

[:lms, :cms].each do |system|
    deprecated("browse_jasmine_#{system}", "test:js:dev", system)
    deprecated("phantomjs_jasmine_#{system}", "test:js:run", system)
    deprecated("jasmine:#{system}", "test:js:run", system)
    deprecated("jasmine:#{system}:browser", "test:js:dev", system)
    deprecated("jasmine:#{system}:browser:watch", "test:js:dev", system)
    deprecated("jasmine:#{system}:phantomjs", "test:js:run", system)
    deprecated("#{system}:check_settings:jasmine", "")
    deprecated("#{system}:gather_assets:jasmine", "")
    deprecated("test_acceptance_#{system}", "test:acceptance:#{system}")
    deprecated("fasttest_acceptance_#{system}", "test:acceptance:#{system}:fast")
end

Dir["common/lib/*"].select{|lib| File.directory?(lib)}.each do |lib|

    if lib == 'common/lib/xmodule' then
        deprecated("browse_jasmine_#{lib}", "test:js:dev", "xmodule")
        deprecated("phantomjs_jasmine_#{lib}", "test:js:run", "xmodule")
    else
        deprecated("browse_jasmine_#{lib}", "test:js:dev")
        deprecated("phantomjs_jasmine_#{lib}", "test:js:run")
    end
end

deprecated("browse_jasmine_discussion", "test:js:dev", "common")
deprecated("phantomjs_jasmine_discussion", "test:js:run", "common")
deprecated("jasmine:common/lib/xmodule", "test:js:run", "xmodule")
deprecated("jasmine:common/lib/xmodule:browser", "test:js:dev", "xmodule")
deprecated("jasmine:common/lib/xmodule:phantomjs", "test:js:run", "xmodule")
deprecated("jasmine:common/static/coffee", "test:js:run", "common")
deprecated("jasmine:common/static/coffee:browser", "test:js:dev", "common")
deprecated("jasmine:common/static/coffee:phantomjs", "test:js:run", "common")

deprecated("jasmine", "test:js")
deprecated("jasmine:phantomjs", "test:js:run")
deprecated("jasmine:browser", "test:js:dev")
deprecated("test_acceptance", "test:acceptance")
