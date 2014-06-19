# Internationalization tasks deprecated to paver

require 'colorize'

def deprecated(deprecated, deprecated_by, *args)

    task deprecated do

        # Need to install paver dependencies for the commands to work!
        sh("pip install -r requirements/edx/paver.txt")

        new_cmd = deprecated_by

        puts("Task #{deprecated} has been deprecated. Using #{deprecated_by} instead.".red)
        sh(new_cmd)
        exit
    end
end

deprecated("i18n:extract", "paver i18n_extract")
deprecated("i18n:generate", "paver i18n_generate")
deprecated("i18n:generate_strict", "paver i18n_generate_strict")
deprecated("i18n:dummy", "paver i18n_dummy")
deprecated("i18n:validate:gettext", "paver i18n_validate_gettext")
deprecated("i18n:validate:transifex_config", "paver i18n_validate_transifex_config")
deprecated("i18n:transifex:push", "paver i18n_transifex_push")
deprecated("i18n:transifex:pull", "paver i18n_transifex_pull")
deprecated("i18n:robot:push", "paver i18n_robot_push")
deprecated("i18n:robot:pull", "paver i18n_robot_pull")
