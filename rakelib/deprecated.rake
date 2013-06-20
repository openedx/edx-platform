
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
end

Dir["common/lib/*"].select{|lib| File.directory?(lib)}.each do |lib|
    deprecated("browse_jasmine_#{lib}", "jasmine:#{lib}:browser")
    deprecated("phantomjs_jasmine_#{lib}", "jasmine:#{lib}:phantomjs")
end

deprecated("browse_jasmine_discussion", "jasmine:common/static/coffee:browser")
deprecated("phantomjs_jasmine_discussion", "jasmine:common/static/coffee:phantomjs")