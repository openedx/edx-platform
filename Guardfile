require 'bourbon'

# Helper method
def production?
  @@options[:group].include? 'production'
end

guard :coffeescript, :name => :jasmine, :input => 'templates/coffee/spec', :all_on_start => production?

guard :coffeescript, :input => 'templates/coffee/src', :noop => true
guard :process, :name => :coffeescript, :command => "coffee -j static/js/application.js -c templates/coffee/src" do
  watch(%r{^templates/coffee/src/(.+)\.coffee$})
end

if production?
  guard :sass, :input => 'templates/sass', :output => 'static/css', :style => :compressed, :all_on_start => true
else
  guard :sass, :input => 'templates/sass', :output => 'static/css', :style => :nested, :line_numbers => true
end
