package io.github.niuuzinho.caderno201;

import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.provider.Settings;
import androidx.core.content.FileProvider;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

/**
 * Baixa o APK da atualização dentro do app e abre o instalador do Android,
 * sem passar pelo navegador.
 */
@CapacitorPlugin(name = "ApkInstaller")
public class ApkInstallerPlugin extends Plugin {

    @PluginMethod
    public void install(final PluginCall call) {
        final String url = call.getString("url");
        if (url == null || !url.startsWith("https://")) {
            call.reject("Endereço de download inválido.");
            return;
        }

        // Android 8+: cada app precisa ser autorizado a instalar outros apps (inclusive ele mesmo).
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                && !getContext().getPackageManager().canRequestPackageInstalls()) {
            Intent settings = new Intent(
                    Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                    Uri.parse("package:" + getContext().getPackageName()));
            settings.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            getContext().startActivity(settings);
            JSObject r = new JSObject();
            r.put("status", "needs_permission");
            call.resolve(r);
            return;
        }

        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    File dir = new File(getContext().getCacheDir(), "updates");
                    if (!dir.exists() && !dir.mkdirs()) {
                        call.reject("Não consegui criar a pasta temporária.");
                        return;
                    }
                    File apk = new File(dir, "Caderno201.apk");
                    if (apk.exists()) apk.delete();

                    HttpURLConnection conn = (HttpURLConnection) new URL(url).openConnection();
                    conn.setInstanceFollowRedirects(true);
                    conn.setConnectTimeout(30000);
                    conn.setReadTimeout(30000);
                    conn.setRequestProperty("User-Agent", "Caderno201");
                    int code = conn.getResponseCode();
                    if (code != 200) {
                        call.reject("O servidor respondeu com o código " + code + ".");
                        return;
                    }
                    long total = conn.getContentLength();
                    long done = 0;
                    int lastPct = -1;
                    InputStream in = conn.getInputStream();
                    FileOutputStream out = new FileOutputStream(apk);
                    byte[] buf = new byte[32768];
                    int n;
                    while ((n = in.read(buf)) != -1) {
                        out.write(buf, 0, n);
                        done += n;
                        int pct = total > 0 ? (int) (done * 100 / total) : -1;
                        if (pct != lastPct) {
                            lastPct = pct;
                            JSObject p = new JSObject();
                            p.put("percent", pct);
                            p.put("received", done);
                            p.put("total", total);
                            notifyListeners("progress", p);
                        }
                    }
                    out.close();
                    in.close();
                    conn.disconnect();

                    if (apk.length() == 0 || (total > 0 && apk.length() != total)) {
                        call.reject("O download não terminou. Tente de novo.");
                        return;
                    }

                    Uri uri = FileProvider.getUriForFile(
                            getContext(), getContext().getPackageName() + ".apkprovider", apk);
                    Intent install = new Intent(Intent.ACTION_VIEW);
                    install.setDataAndType(uri, "application/vnd.android.package-archive");
                    install.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_ACTIVITY_NEW_TASK);
                    getContext().startActivity(install);

                    JSObject r = new JSObject();
                    r.put("status", "installing");
                    call.resolve(r);
                } catch (Exception e) {
                    call.reject(e.getMessage() != null ? e.getMessage() : e.toString());
                }
            }
        }).start();
    }
}
