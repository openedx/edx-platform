# acceptance test tasks deprecated to paver

require 'colorize'

def deprecated(deprecated, deprecated_by,  *args)

    task deprecated, [:harvest_args] do |t,args|

        # Need to install paver dependencies for the commands to work!
        sh("pip install -r requirements/edx/paver.txt")

        args.with_defaults(:harvest_args => nil)
        new_cmd = deprecated_by

        if !args.harvest_args.nil?
            new_cmd = "#{new_cmd} --extra_args='#{args.harvest_args}'"
        end

        puts("Task #{deprecated} has been deprecated. Use #{new_cmd} instead.".red)
        sh(new_cmd)
    end
end

deprecated("test:acceptance", "paver test_acceptance")
deprecated("test:acceptance:cms", "paver test_acceptance -s cms")
deprecated("test:acceptance:cms:fast", "paver test_acceptance -s cms --fasttest")
deprecated("test:acceptance:lms", "paver test_acceptance -s lms")
deprecated("test:acceptance:lms:fast", "paver test_acceptance -s lms --fasttest")
