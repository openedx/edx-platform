require 'bundler/gem_tasks'
require 'rake/testtask'

Rake::TestTask.new   do |t|
  t.libs = ['lib','tests']
  t.test_files = Dir.glob('tests/**/*_test.rb').sort
  t.verbose = false
  t.options = "- --tapy | tapout navigator --require tapout/reporters/navigator_reporter"
end

task :default => :test

desc 'Re-render all test Sass files to new control files.'
task 'render' => ['environment'] do
  require File.expand_path('../tests/navigator', __FILE__)
  Navigator::Renderer.render_controls
end

task 'environment' do
  lib = File.expand_path('../lib', __FILE__)
  $LOAD_PATH.unshift(lib) unless $LOAD_PATH.include?(lib)
  require 'sassy-maps'
end
