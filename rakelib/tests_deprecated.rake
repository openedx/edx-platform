# tests deprecated to paver

require 'colorize'

def deprecated(deprecated, deprecated_by,  *args)

    task deprecated, [:test_id] do |t,args|

        args.with_defaults(:test_id => nil)

        if deprecated.include? "cms"
            system = "--system=cms"
        elsif deprecated.include? "lms"
            system = "--system=lms"
        else
            system = ""
        end

        new_cmd = "#{deprecated_by} #{system}"

        if !args.test_id.nil?
            new_cmd = "#{new_cmd} --test_id=#{args.test_id}"
        end

        puts("Task #{deprecated} has been deprecated. Use #{new_cmd} instead. Waiting 5 seconds...".red)
        sleep(5)
        sh(new_cmd)
        exit
    end
end

deprecated("test_docs", "paver test_docs")
deprecated("test_cms", "paver test_system")
deprecated("test_lms", "paver test_system")
deprecated("fasttest_cms", "paver fasttest")
deprecated("fasttest_lms", "paver fasttest")

deprecated("test", "paver test")

deprecated("coverage", "paver coverage")

Dir["common/lib/*"].select{|lib| File.directory?(lib)}.each do |lib|

    deprecated("test_#{lib}", "paver test_lib --lib=#{lib}")
    deprecated("fasttest_#{lib}", "paver test_lib --lib=#{lib}")

end
