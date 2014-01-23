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

deprecated("i18n:dummy", "paver i18n_dummy")
deprecated("i18n:extract", "paver i18m_extract")
deprecated("i18n:generate", "paver i18m_generate")
deprecated("i18n:test", "paver i18m_test")
deprecated("i18n:transifex:pull", "paver i18m_transifex_pull")
deprecated("i18n:transifex:push", "paver i18m_transifex_push")
deprecated("i18n:transifex:gettext", "paver i18m_transifex_gettext")
deprecated("i18n:validate:transifex:config", "paver i18m_validate_transifex_config")

