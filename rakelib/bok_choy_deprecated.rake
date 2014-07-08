# test tasks deprecated to paver

require 'colorize'

def deprecated(deprecated, deprecated_by, *args)

    task deprecated, [:test_spec] do |t,args|

        args.with_defaults(:test_spec => nil)

        new_cmd = "#{deprecated_by}"

        if !args.test_spec.nil?
            new_cmd = "#{new_cmd} -t #{args.test_spec}"
        end

        puts("Task #{deprecated} has been deprecated. Using #{new_cmd} instead.".red)
        sh(new_cmd)
    end
end

deprecated('test:bok_choy', 'paver test_bokchoy')
deprecated('test:bok_choy:coverage', 'paver bokchoy_coverage')
deprecated('test:bok_choy:fast', 'paver test_bokchoy --fasttest')
deprecated('test:bok_choy:setup', 'paver test_bokchoy')
