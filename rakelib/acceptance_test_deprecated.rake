# acceptance tests deprecated to paver

require 'colorize'

def deprecated(deprecated, deprecated_by, *args)

    task deprecated, [:harvest_args] do |t,args|

        args.with_defaults(:harvest_args => nil)

        if deprecated.include? "cms"
            system = "--system=cms"
        elsif deprecated.include? "lms"
            system = "--system=lms"
        else
            system = ""
        end

        new_cmd = "#{deprecated_by} #{system}"

        if !args.harvest_args.nil?
            new_cmd = "#{new_cmd} --harvest_args=#{args.harvest_args}"
        end

        puts("Task #{deprecated} has been deprecated. Use #{new_cmd} instead. Waiting 5 seconds...".red)
        sleep(5)
        sh(new_cmd)
        exit
    end
end

deprecated("test:acceptance:cms", "paver test_acceptance")
deprecated("test:acceptance:lms", "paver test_acceptance")
deprecated("test:acceptance:cms:fast", "paver test_acceptance_fast")
deprecated("test:acceptance:lms:fast", "paver test_acceptance_fast")
deprecated("test:acceptance", "paver test_acceptance_all")

