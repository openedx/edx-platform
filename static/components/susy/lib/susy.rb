base_directory  = File.expand_path(File.join(File.dirname(__FILE__), '..'))
susy_stylesheets_path = File.join(base_directory, 'sass')
susy_templates_path = File.join(base_directory, 'templates')

if (defined? Compass)
  Compass::Frameworks.register('susy', :stylesheets_directory => susy_stylesheets_path, :templates_directory => susy_templates_path)
else
  # compass not found, register on the Sass path via the environment.
  if ENV.has_key?("SASS_PATH")
    ENV["SASS_PATH"] = ENV["SASS_PATH"] + File::PATH_SEPARATOR + susy_stylesheets_path
  else
    ENV["SASS_PATH"] = susy_stylesheets_path
  end
end
