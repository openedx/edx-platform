# acceptance tests deprecated to paver

require 'colorize'

def deprecated(deprecated, deprecated_by)

    task deprecated do
        puts("Task #{deprecated} has been deprecated. Use #{deprecated_by} instead. Waiting 5 seconds...".red)
        sleep(5)
        sh(deprecated_by)
        exit
    end
end

deprecated("ws:migrate", "paver ws_migrate")
