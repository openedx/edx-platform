# js_test tasks deprecated to paver

require 'colorize'

def deprecated(deprecated, deprecated_by,  *args)

    task deprecated, [:env] do |t,args|

        args.with_defaults(:env => nil)

        new_cmd = "#{deprecated_by}"

        if !args.env.nil?
            new_cmd = "#{new_cmd} --suite=#{args.env}"
        end

        puts("Task #{deprecated} has been deprecated. Using #{new_cmd} instead.".red)
        sh(new_cmd)
    end
end

# deprecates all js_test.rake tasks 
deprecated('test:js', 'paver test_js')
deprecated('test:js:coverage', 'paver test_js -c')
deprecated('test:js:dev', 'paver test_js_dev')
deprecated('test:js:run', 'paver test_js_run')
