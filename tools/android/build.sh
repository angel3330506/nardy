#!/usr/bin/env bash
# Сборка Android-приложения «Нарды» (для RuStore): подписанные APK и AAB.
# Приложение открывает игру с сайта (как айфоновское): обновления игры приходят сами, пересобирать нужно только при смене оболочки.
# Нужно: ANDROID_HOME (SDK: platforms;android-35, build-tools;35.0.0), Java 21, Node 20.
# Ключ подписи (хранить вечно! без него в RuStore не выпустить обновление): KEYSTORE=путь.jks KS_PASS=пароль KEY_ALIAS=nardy
# Запуск из корня репозитория: tools/android/build.sh <папка_сборки> [versionCode] [versionName]
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd); OUT=$(mkdir -p "$1" && cd "$1" && pwd); VC=${2:-1}; VN=${3:-1.0}
cd "$OUT"; rm -rf app; mkdir app; cd app
npm init -y >/dev/null
npm i -s @capacitor/core@7 @capacitor/cli@7 @capacitor/android@7 @capacitor/haptics@7 @capacitor/app@7 @capacitor/share@7 @capacitor/filesystem@7 "$ROOT"/android-shell/nardy-ads
mkdir www && cp -R "$ROOT"/index.html "$ROOT"/boards "$ROOT"/sounds "$ROOT"/icons www/   # запасная копия игры (если сайт недоступен)
cp "$ROOT"/android-shell/capacitor.config.json .
npx cap add android >/dev/null
J=android/app/src/main/java/am/nardy/game; cp "$ROOT"/android-shell/MainActivity.java $J/MainActivity.java
M=android/app/src/main/AndroidManifest.xml
# только горизонтально (обе стороны)
sed -i 's/<activity/<activity android:screenOrientation="sensorLandscape"/' $M
# версия
G=android/app/build.gradle
sed -i "s/versionCode [0-9]*/versionCode $VC/; s/versionName \"[^\"]*\"/versionName \"$VN\"/" $G
# иконки и экран загрузки из тех же картинок, что у айфона
python3 - "$ROOT" <<'PY'
import sys, os, glob
from PIL import Image, ImageDraw
root=sys.argv[1]; res='android/app/src/main/res'
ic=Image.open(f'{root}/ios-shell/AppIcon-1024.png').convert('RGBA')
for d,px in {'mdpi':48,'hdpi':72,'xhdpi':96,'xxhdpi':144,'xxxhdpi':192}.items():
    im=ic.resize((px,px),Image.LANCZOS); im.save(f'{res}/mipmap-{d}/ic_launcher.png')
    m=Image.new('L',(px*4,px*4),0); ImageDraw.Draw(m).ellipse((0,0,px*4-1,px*4-1),fill=255); m=m.resize((px,px),Image.LANCZOS)
    r=im.copy(); r.putalpha(m); r.save(f'{res}/mipmap-{d}/ic_launcher_round.png')
    # адаптивная иконка: передний план — та же картинка с полями (система обрезает края)
    fg=Image.new('RGBA',(int(px*2.25),int(px*2.25)),(0,0,0,0)); s=int(px*1.5); fg.paste(ic.resize((s,s),Image.LANCZOS),((fg.width-s)//2,)*2)
    fg.save(f'{res}/mipmap-{d}/ic_launcher_foreground.png')
open(f'{res}/values/ic_launcher_background.xml','w').write('<?xml version="1.0" encoding="utf-8"?>\n<resources><color name="ic_launcher_background">#2a1a10</color></resources>\n')
sp=Image.open(f'{root}/ios-shell/splash-2732.png').convert('RGB')
for f in glob.glob(f'{res}/drawable*/splash.png'):
    w,h=Image.open(f).size; s=max(w,h); im=sp.resize((s,s),Image.LANCZOS); im.crop(((s-w)//2,(s-h)//2,(s-w)//2+w,(s-h)//2+h)).save(f)
PY
npx cap sync android >/dev/null
# подпись
cat >> $G <<GR
android { signingConfigs { release { storeFile file(System.getenv('KEYSTORE')); storePassword System.getenv('KS_PASS'); keyAlias System.getenv('KEY_ALIAS') ?: 'nardy'; keyPassword System.getenv('KS_PASS') } }
  buildTypes { release { signingConfig signingConfigs.release } } }
GR
cd android && ./gradlew -q --init-script "$ROOT/tools/android/mirror.gradle" assembleRelease bundleRelease
cp app/build/outputs/apk/release/app-release.apk "$OUT/Nardy-$VN.apk"; cp app/build/outputs/bundle/release/app-release.aab "$OUT/Nardy-$VN.aab"
ls -la "$OUT"/Nardy-*
