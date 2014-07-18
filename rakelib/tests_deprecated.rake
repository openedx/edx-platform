# test tasks deprecated to paver

require 'colorize'

def deprecated(deprecated, deprecated_by, use_id, *args)

    task deprecated, [:test_id] do |t,args|

        args.with_defaults(:test_id => nil)

        new_cmd = "#{deprecated_by}"

        if !args.test_id.nil? && use_id
            new_cmd = "#{new_cmd} --test_id=#{args.test_id}"
        end

        puts("Task #{deprecated} has been deprecated. Using #{new_cmd} instead.".red)
        sh(new_cmd)
    end
end

# deprecates all test.rake tasks
deprecated("test", "paver test", false)
deprecated('test:python', 'paver test_python', false)

deprecated("test_cms", "paver test_system -s cms", true)
deprecated("test_lms", "paver test_system -s lms", true)
deprecated("fasttest_cms", "paver test_system -s cms --fasttest", true)
deprecated("fasttest_lms", "paver test_system -s lms --fasttest", true)

Dir["common/lib/*"].select{|lib| File.directory?(lib)}.each do |lib|

    deprecated("test_#{lib}", "paver test_lib --lib=#{lib}", true)
    deprecated("fasttest_#{lib}", "paver test_lib --lib=#{lib}", true)

end

deprecated("coverage", "paver coverage", false)

deprecated("clean_reports_dir", "paver clean_reports_dir", false)
deprecated("clean_test_files", "paver clean_test_files", false)
deprecated("test:clean_mongo", "paver clean_mongo", false)
