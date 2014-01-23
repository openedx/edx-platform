# acceptance tests deprecated to paver

require 'colorize'

def deprecated(deprecated, deprecated_by)

    task deprecated, [:suite] do |t,args|

        args.with_defaults(:suite => "dev")
        new_cmd = deprecated_by + " --suite=#{args.env}"

        puts("Task #{deprecated} has been deprecated. Use #{deprecated_by} instead. Waiting 5 seconds...".red)
        sleep(5)
        sh(new_cmd)
        exit
    end
end

deprecated("test:js", "paver test_js")
deprecated("test:js:coverage", "paver test_js_coverage")
deprecated("test:js:dev", "paver test_js_dev")
deprecated("test:js:run", "paver test_js_run")

