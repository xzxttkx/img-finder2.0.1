[app]

title = Duplicate Image Finder
package.name = duplicateimagefinder
package.domain = org.dupfinder
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
source.include_patterns = assets/*
source.exclude_exts = spec
source.exclude_dirs = tests,bin,venv,.git
source.exclude_patterns = license,images/*/*.jpg
version = 1.0.0
requirements = python3,kivy,pillow
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, MANAGE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 26
android.sdk = 33
android.sdk_path = /usr/local/lib/android/sdk
android.build_mode = debug
android.archs = arm64-v8a, armeabi-v7a
android.use_androidx = True

[buildozer]
log_level = 1
warn_on_root = 1
