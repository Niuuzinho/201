#!/usr/bin/env python3
"""Coloca o instalador interno de atualizações no projeto Android gerado pelo Capacitor.

Uso (a partir da raiz do repositório): python3 android-recursos/nativo/aplicar.py
"""
import json, os, re, shutil, sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AQUI = os.path.join(RAIZ, 'android-recursos', 'nativo')
ANDROID = os.path.join(RAIZ, 'android')

app_id = json.load(open(os.path.join(RAIZ, 'capacitor.config.json'), encoding='utf-8'))['appId']
pacote = os.path.join(ANDROID, 'app', 'src', 'main', 'java', *app_id.split('.'))
if not os.path.isdir(pacote):
    sys.exit('pasta do pacote não encontrada: ' + pacote)

for nome in ('ApkInstallerPlugin.java', 'MainActivity.java'):
    texto = open(os.path.join(AQUI, nome), encoding='utf-8').read()
    texto = re.sub(r'^package .*;', 'package ' + app_id + ';', texto, count=1, flags=re.M)
    open(os.path.join(pacote, nome), 'w', encoding='utf-8').write(texto)

xml_dir = os.path.join(ANDROID, 'app', 'src', 'main', 'res', 'xml')
os.makedirs(xml_dir, exist_ok=True)
shutil.copy(os.path.join(AQUI, 'apk_paths.xml'), os.path.join(xml_dir, 'apk_paths.xml'))

manifesto = os.path.join(ANDROID, 'app', 'src', 'main', 'AndroidManifest.xml')
m = open(manifesto, encoding='utf-8').read()
if 'REQUEST_INSTALL_PACKAGES' not in m:
    m = m.replace('</manifest>', '    <uses-permission android:name="android.permission.REQUEST_INSTALL_PACKAGES" />\n</manifest>', 1)
if '.apkprovider' not in m:
    provider = '''        <provider
            android:name="androidx.core.content.FileProvider"
            android:authorities="${applicationId}.apkprovider"
            android:exported="false"
            android:grantUriPermissions="true">
            <meta-data
                android:name="android.support.FILE_PROVIDER_PATHS"
                android:resource="@xml/apk_paths" />
        </provider>
'''
    m = m.replace('</application>', provider + '    </application>', 1)
assert 'REQUEST_INSTALL_PACKAGES' in m and '.apkprovider' in m, 'não consegui alterar o AndroidManifest.xml'
open(manifesto, 'w', encoding='utf-8').write(m)
print('instalador interno aplicado em', pacote)
