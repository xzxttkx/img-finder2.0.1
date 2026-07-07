[app]

# (str) Title of your application
title = Duplicate Image Finder

# (str) Package name
package.name = duplicateimagefinder

# (str) Package domain (needed for android/ios packaging)
package.domain = org.dupfinder

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,ttf

# (list) List of inclusions using pattern matching
source.include_patterns = assets/*

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_exts = spec

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests,bin,venv,.git

# (list) List of exclusions using pattern matching
source.exclude_patterns = license,images/*/*.jpg

# (str) Application versioning (method 1)
version = 1.0.0

# (str) Application versioning (method 2)
# version.regex = __version__ = ['"](.*)['"]
# version.filename = %(source.dir)s/main.py

# (list) Application requirements
# comma separated e.g. requirements = sqlite3, kivy
requirements = python3,kivy,pillow

# (str) Custom source folders for requirements
# Sets custom source for any requirements with recipes
# requirements.source.kivy = ../../kivy

# (str) Presplash of the application
# presplash.filename = %(source.dir)s/assets/presplash.png

# (str) Icon of the application
# icon.filename = %(source.dir)s/assets/icon.png

# (list) Permissions
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, READ_MEDIA_IMAGES, MANAGE_EXTERNAL_STORAGE

# (list) Features (adds uses-feature -tags to manifest)
# android.features = android.hardware.usb.host

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 26

# (int) Android SDK version to use
# android.sdk = 33

# (str) Android NDK version to use
# android.ndk = 25b

# (int) Android NDK API to use. This is the minimum API your app will support.
# android.ndk_api = 21

# (bool) Use private storage. If True, files will be stored in the app's
# private directory on external storage (Android/data/...).
# android.private_storage = True

# (str) Android NDK directory (if empty, it will be automatically downloaded.)
# android.ndk_path =

# (str) Android SDK directory (if empty, it will be automatically downloaded.)
# android.sdk_path =

# (str) python-for-android branch to use, defaults to master
p4a.branch = develop

# (str) python-for-android specific fork to use, defaults to upstream
# p4a.fork = kivy

# (str) python-for-android git clone directory (if empty, it will be automatically cloned from github)
# p4a.source_dir =

# (str) The directory in which python-for-android should look for your own build recipes (if any)
# p4a.local_recipes =

# (str) Filename to the hook for p4a
# p4a.hook =

# (str) Bootstrap to use for android builds
# p4a.bootstrap = sdl2

# (list) List of Java classes that should be added to the generated classes.dex file.
# This may be needed for certain APIs (e.g., Google Play Services).
# android.add_gradle_dependencies =

# (list) Gradle dependencies to add
# android.gradle_dependencies =

# (list) Java classes to add as activities to the manifest
# android.add_activities =

# (list) Java classes to add as services to the manifest
# android.add_services =

# (list) List of Java .jar files to add to the libs
# android.add_jars =

# (str) python-for-android wheel to use for Android builds
# p4a.wheel =

# (list) Build options to pass to python-for-android
# p4a.build_options =

# (bool) Whether to run Android builds in debug mode (True) or release mode (False)
android.build_mode = debug

# (str) Android logcat filters to use
# android.logcat_filters = *:S python:D

# (bool) Copy library instead of making big libpymodules.so
# android.copy_libs = 1

# (list) The Android architecture(s) to build for
android.archs = arm64-v8a, armeabi-v7a

# (int) overrides automatic versionCode computation (used in build.gradle)
# this is not the same as app version and should only be edited if you know what you're doing
# android.numeric_version = 1

# (str) Android pre-compiled python path
# android.precompiled_python =

# (bool) Enables Android App Bundle format
# android.app_bundle = False

# (bool) Enable AndroidX support
android.use_androidx = True

# (bool) Enable signing of the APK for release builds
# android.release = False

# (str) Key store path for release signing
# android.release_artifact = aab

# (str) Key alias for release signing
# android.signing_alias =

# (str) Key store password for release signing
# android.signing_keystore_pass =

# (str) Key alias password for release signing
# android.signing_alias_pass =

# -- NDK API level (minimum) --
# android.ndk_api = 21


[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with full debug output))
log_level = 1

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1

# (str) Path to build artifact storage, absolute or relative to spec file
# build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .aab) storage
# bin_dir = ./bin
