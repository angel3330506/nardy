Pod::Spec.new do |s|
  s.name = 'NardyNative'
  s.version = '1.0.0'
  s.summary = 'Native helpers for Nardy'
  s.license = 'MIT'
  s.homepage = 'https://angel3330506.github.io/nardy/'
  s.author = 'Nardy'
  s.source = { :git => 'https://github.com/angel3330506/nardy.git', :tag => s.version.to_s }
  s.source_files = 'ios/Plugin/**/*.{swift,h,m}'
  s.ios.deployment_target = '14.0'
  s.dependency 'Capacitor'
  s.swift_version = '5.1'
end
