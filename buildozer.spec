[app]
title = Manga Downloader
package.name = mangadownloader
package.domain = org.manga
source.dir = .
source.main = manga_downloader.py
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

requirements = python3,kivy,requests,pillow

orientation = portrait
fullscreen = 0

android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a

[buildozer]
log_level = 2
