# --- Internationalization tasks

namespace :i18n do

  desc "Extract localizable strings from sources"
  task :extract => "i18n:validate:gettext" do
    sh(File.join(REPO_ROOT, "i18n", "extract.py"))
  end

  desc "Compile localizable strings from sources, extracting strings first."
  task :generate => "i18n:extract" do
    sh(File.join(REPO_ROOT, "i18n", "generate.py"))
  end

  desc "Simulate international translation by generating dummy strings corresponding to source strings."
  task :dummy do
    source_files = Dir["#{REPO_ROOT}/conf/locale/en/LC_MESSAGES/*.po"]
    dummy_locale = 'eo'
    cmd = File.join(REPO_ROOT, "i18n", "make_dummy.py")
    for file in source_files do
      sh("#{cmd} #{file} #{dummy_locale}")
    end
  end

  namespace :validate do

    desc "Make sure GNU gettext utilities are available"
    task :gettext do
      begin
        select_executable('xgettext')
      rescue
        msg = "Cannot locate GNU gettext utilities, which are required by django for internationalization.\n"
        msg += "(see https://docs.djangoproject.com/en/dev/topics/i18n/translation/#message-files)\n"
        msg += "Try downloading them from http://www.gnu.org/software/gettext/"
        abort(msg.red)
      end
    end

    desc "Make sure config file with username/password exists"
    task :transifex_config do
      config_file = "#{Dir.home}/.transifexrc"
      if !File.file?(config_file) or File.size(config_file)==0
        msg ="Cannot connect to Transifex, config file is missing or empty: #{config_file}\n"
        msg += "See http://help.transifex.com/features/client/#transifexrc"
        abort(msg.red)
      end
    end
  end

  namespace :transifex do
    desc "Push source strings to Transifex for translation"
    task :push => "i18n:validate:transifex_config" do
      cmd = File.join(REPO_ROOT, "i18n", "transifex.py")
      sh("#{cmd} push")
    end

    desc "Pull translated strings from Transifex"
    task :pull => "i18n:validate:transifex_config" do
      cmd = File.join(REPO_ROOT, "i18n", "transifex.py")
      sh("#{cmd} pull")
    end
  end

  desc "Run tests for the internationalization library"
  task :test => ["i18n:validate:gettext", "i18n:extract", "i18n:generate"] do
    test = File.join(REPO_ROOT, "i18n", "tests")
    pythonpath_prefix = "PYTHONPATH=#{REPO_ROOT}/i18n:$PYTHONPATH"
    sh("#{pythonpath_prefix} nosetests #{test}")
  end

end
