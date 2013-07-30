default_options = {
    :lms => '8000',
    :cms => '8001',
}

task :predjango => :install_python_prereqs do
    sh("find . -type f -name *.pyc -delete")
    sh('pip install -q --no-index -r requirements/edx/local.txt')
end


task :fastlms do
    # this is >2 times faster that rake [lms], and does not need web, good for local dev
    sh("./manage.py lms runserver --traceback")
end

# Start :system locally with the specified :env and :options.
#
# This task should be invoked via the wrapper below, so we don't
# include a description to keep it from showing up in rake -T.
task :runserver, [:system, :env, :options] => [:install_prereqs, 'assets:_watch', :predjango] do |t, args|
    sh(django_admin(args.system, args.env, 'runserver', args.options))
end

[:lms, :cms].each do |system|
    desc <<-desc
        Start the #{system} locally with the specified environment (defaults to dev).
        Other useful environments are devplus (for dev testing with a real local database)
        desc
    task system, [:env, :options] do |t, args|
        args.with_defaults(:env => 'dev', :options => default_options[system])
        Rake::Task[:runserver].invoke(system, args.env, args.options)
    end

    desc "Start #{system} Celery worker"
    task "#{system}_worker", [:options] => [:predjango] do |t, args|
      args.with_defaults(:options => default_options[system])
      command = 'celery worker'
      sh("./manage.py #{system} --settings dev_with_worker #{command} --loglevel=INFO #{args.join(' ')}")
    end

    # Per environment tasks
    environments(system).each do |env|
        desc "Attempt to import the settings file #{system}.envs.#{env} and report any errors"
        task "#{system}:check_settings:#{env}" => :predjango do
            sh("echo 'import #{system}.envs.#{env}' | #{django_admin(system, env, 'shell')}")
        end
    end
end

desc "Reset the relational database used by django. WARNING: this will delete all of your existing users"
task :resetdb, [:env] do |t, args|
    args.with_defaults(:env => 'dev')
    sh(django_admin(:lms, args.env, 'syncdb'))
    sh(django_admin(:lms, args.env, 'migrate'))
end

task :runserver => :lms

desc "Run django-admin <action> against the specified system and environment"
task "django-admin", [:action, :system, :env, :options] do |t, args|
    # If no system was explicitly set, we want to run both CMS and LMS for migrate and syncdb.
    no_system_set = !args.system
    args.with_defaults(:env => 'dev', :system => 'lms', :options => '')
    sh(django_admin(args.system, args.env, args.action, args.options))
    if no_system_set and (args.action == 'migrate' or args.action == 'syncdb')
      sh(django_admin('cms', args.env, args.action, args.options))
    end
end

desc "Set the staff bit for a user"
task :set_staff, [:user, :system, :env] do |t, args|
    args.with_defaults(:env => 'dev', :system => 'lms', :options => '')
    sh(django_admin(args.system, args.env, 'set_staff', args.user))
end

namespace :cms do
  desc "Clone existing MongoDB based course"
  task :clone do

    if ENV['SOURCE_LOC'] and ENV['DEST_LOC']
      sh(django_admin(:cms, :dev, :clone, ENV['SOURCE_LOC'], ENV['DEST_LOC']))
    else
      raise "You must pass in a SOURCE_LOC and DEST_LOC parameters"
    end
  end

  desc "Delete existing MongoDB based course"
  task :delete_course do

    if ENV['LOC'] and ENV['COMMIT']
        sh(django_admin(:cms, :dev, :delete_course, ENV['LOC'], ENV['COMMIT']))
    elsif ENV['LOC']
      sh(django_admin(:cms, :dev, :delete_course, ENV['LOC']))
    else
      raise "You must pass in a LOC parameter"
    end
  end

  desc "Import course data within the given DATA_DIR variable"
  task :import do
    if ENV['DATA_DIR'] and ENV['COURSE_DIR']
      sh(django_admin(:cms, :dev, :import, ENV['DATA_DIR'], ENV['COURSE_DIR']))
    elsif ENV['DATA_DIR']
      sh(django_admin(:cms, :dev, :import, ENV['DATA_DIR']))
    else
      raise "Please specify a DATA_DIR variable that point to your data directory.\n" +
        "Example: \`rake cms:import DATA_DIR=../data\`"
    end
  end

  desc "Import course data within the given DATA_DIR variable"
  task :xlint do
    if ENV['DATA_DIR'] and ENV['COURSE_DIR']
      sh(django_admin(:cms, :dev, :xlint, ENV['DATA_DIR'], ENV['COURSE_DIR']))
    elsif ENV['DATA_DIR']
      sh(django_admin(:cms, :dev, :xlint, ENV['DATA_DIR']))
    else
      raise "Please specify a DATA_DIR variable that point to your data directory.\n" +
        "Example: \`rake cms:import DATA_DIR=../data\`"
    end
  end

  desc "Export course data to a tar.gz file"
  task :export do
    if ENV['COURSE_ID'] and ENV['OUTPUT_PATH']
      sh(django_admin(:cms, :dev, :export, ENV['COURSE_ID'], ENV['OUTPUT_PATH']))
    else
      raise "Please specify a COURSE_ID and OUTPUT_PATH.\n" +
        "Example: \`rake cms:export COURSE_ID=MITx/12345/name OUTPUT_PATH=foo.tar.gz\`"
    end
  end
end
