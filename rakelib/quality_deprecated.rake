# acceptance tests deprecated to paver

require 'colorize'

def deprecated(deprecated, deprecated_by)

    task deprecated do

        if deprecated.include? "extract" and ARGV.last.downcase == 'extract'
            new_cmd = deprecated_by + " --extract"
        else
            new_cmd = deprecated_by
        end

        puts("Task #{deprecated} has been deprecated. Use #{deprecated_by} instead. Waiting 5 seconds...".red)
        sleep(5)
        sh(new_cmd)
        exit
    end
end



deprecated("pep8:cms", "paver run_pep8 --system=cms")
deprecated("pep8:lms", "paver run_pep8 --system=lms")
deprecated("pep8:common", "paver run_pep8 --system=common")


deprecated("pylint:cms", "paver run_pylint --system=cms")
deprecated("pylint:lms", "paver run_pylint --system=lms")
deprecated("pylint:common", "paver run_pylint --system=common")

deprecated("pylint:cms:errors", "paver run_pylint --system=cms --errors")
deprecated("pylint:lms:errors", "paver run_pylint --system=lms --errors")
deprecated("pylint:common:errors", "paver run_pylint --system=common --errors")

deprecated("quality", "paver run_quality")

