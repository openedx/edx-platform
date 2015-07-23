require 'sassy-maps/version'
require 'sass'

sassy_maps_path = File.expand_path('../../sass', __FILE__)

if (defined? Compass)
  Compass::Frameworks.register(
    'sassy-maps',
    :stylesheets_directory => sassy_maps_path
  )
else
  ENV["SASS_PATH"] = [ENV["SASS_PATH"], sassy_maps_path].compact.join(File::PATH_SEPARATOR)
end

module SassyMaps
end
