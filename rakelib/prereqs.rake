PREREQS_MD5_DIR = ENV["PREREQ_CACHE_DIR"] || File.join(REPO_ROOT, '.prereqs_cache')

CLOBBER.include(PREREQS_MD5_DIR)

directory PREREQS_MD5_DIR

desc "Install all prerequisites needed for the lms and cms"
task :install_prereqs => [:install_node_prereqs, :install_ruby_prereqs, :install_python_prereqs]

desc "Install all node prerequisites for the lms and cms"
task :install_node_prereqs => "ws:migrate" do
    unchanged = 'Node requirements unchanged, nothing to install'
    when_changed(unchanged, ['package.json']) do
        sh('npm install')
    end unless ENV['NO_PREREQ_INSTALL']
end

desc "Install all ruby prerequisites for the lms and cms"
task :install_ruby_prereqs => "ws:migrate" do
    unchanged = 'Ruby requirements unchanged, nothing to install'
    when_changed(unchanged, ['Gemfile']) do
        sh('bundle install')
    end unless ENV['NO_PREREQ_INSTALL']
end

desc "Install all python prerequisites for the lms and cms"
task :install_python_prereqs => "ws:migrate" do
    site_packages_dir = `python -c 'import os; import distutils.sysconfig as dusc; print dusc.get_python_lib()'`.chomp
    unchanged = 'Python requirements unchanged, nothing to install'
    when_changed(unchanged, ['requirements/**/*'], [site_packages_dir]) do
        ENV['PIP_DOWNLOAD_CACHE'] ||= '.pip_download_cache'
        sh('pip install --exists-action w -r requirements/edx/pre.txt')
        sh('pip install --exists-action w -r requirements/edx/base.txt')
        sh('pip install --exists-action w -r requirements/edx/post.txt')
        sh('python -m nltk.downloader stopwords wordnet')
        # requirements/private.txt is used to install our libs as
        # working dirs, or for personal-use tools.
        if File.file?("requirements/private.txt")
            sh('pip install -r requirements/private.txt')
        end
    end unless ENV['NO_PREREQ_INSTALL']
end
