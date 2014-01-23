# assets tasks deprecated to paver

require 'colorize'

def deprecated(deprecated, deprecated_by,  *args)

    task deprecated, [:test_spec] do |t,args|

        args.with_defaults(:test_spec => nil)

        if !args.test_spec.nil?
            new_cmd = deprecated_by + " --test_spec=#{args.test_spec}"
        else
            new_cmd = deprecated_by
        end

        puts("Task #{deprecated} has been deprecated. Use #{new_cmd} instead. Waiting 5 seconds...".red)
        sleep(5)
        sh(new_cmd)
        exit
    end
end

deprecated("test:bok_choy", "paver test_bok_choy")
deprecated("test:bok_choy:fast", "paver test_bok_choy_fast")
deprecated("test:bok_choy:setup", "paver bok_choy_setup")


