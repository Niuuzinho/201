package io.github.niuuzinho.caderno201;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.Build;
import android.provider.Settings;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import androidx.core.content.FileProvider;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import org.json.JSONObject;

/**
 * Baixa o APK da atualização dentro do app e abre o instalador do Android,
 * sem passar pelo navegador. É chamado pela página como window.AndroidUpdater.
 * O andamento volta para a página por window.__updEvent({ type, ... }).
 */
public class AndroidUpdater {
    private final Activity activity;
    private final WebView web;

    public AndroidUpdater(Activity activity, WebView web) {
        this.activity = activity;
        this.web = web;
    }

    @JavascriptInterface
    public String ping() {
        return "ok";
    }

    @JavascriptInterface
    public void install(final String url) {
        if (url == null || !url.startsWith("https://")) {
            emit("error", "Endereço de download inválido.", -1);
            return;
        }

        // Android 8+: cada app precisa ser autorizado a instalar outros apps (inclusive ele mesmo).
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                && !activity.getPackageManager().canRequestPackageInstalls()) {
            activity.runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    try {
                        Intent settings = new Intent(
                                Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                                Uri.parse("package:" + activity.getPackageName()));
                        activity.startActivity(settings);
                    } catch (Exception e) {
                        // a página mostra o aviso mesmo assim
                    }
                }
            });
            emit("needs_permission", "", -1);
            return;
        }

        new Thread(new Runnable() {
            @Override
            public void run() {
                try {
                    download(url);
                } catch (Exception e) {
                    emit("error", e.getMessage() != null ? e.getMessage() : e.toString(), -1);
                }
            }
        }).start();
    }

    private void download(String url) throws Exception {
        File dir = new File(activity.getCacheDir(), "updates");
        if (!dir.exists() && !dir.mkdirs()) throw new Exception("Não consegui criar a pasta temporária.");
        final File apk = new File(dir, "Caderno201.apk");
        if (apk.exists()) apk.delete();

        HttpURLConnection conn = (HttpURLConnection) new URL(url).openConnection();
        conn.setInstanceFollowRedirects(true);
        conn.setConnectTimeout(30000);
        conn.setReadTimeout(30000);
        conn.setRequestProperty("User-Agent", "Caderno201");
        int code = conn.getResponseCode();
        if (code != 200) throw new Exception("O servidor respondeu com o código " + code + ".");

        long total = conn.getContentLength();
        long done = 0;
        int lastPct = -2;
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
                emit("progress", "", pct);
            }
        }
        out.close();
        in.close();
        conn.disconnect();

        if (apk.length() == 0 || (total > 0 && apk.length() != total)) {
            throw new Exception("O download não terminou. Tente de novo.");
        }

        activity.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                try {
                    Uri uri = FileProvider.getUriForFile(
                            activity, activity.getPackageName() + ".apkprovider", apk);
                    Intent install = new Intent(Intent.ACTION_VIEW);
                    install.setDataAndType(uri, "application/vnd.android.package-archive");
                    install.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
                    activity.startActivity(install);
                    emit("done", "", 100);
                } catch (Exception e) {
                    emit("error", "Não consegui abrir o instalador: " + e, -1);
                }
            }
        });
    }

    private void emit(String type, String message, int percent) {
        try {
            JSONObject o = new JSONObject();
            o.put("type", type);
            o.put("message", message);
            o.put("percent", percent);
            final String js = "window.__updEvent && window.__updEvent(" + o.toString() + ")";
            web.post(new Runnable() {
                @Override
                public void run() {
                    web.evaluateJavascript(js, null);
                }
            });
        } catch (Exception e) {
            // sem como avisar a página
        }
    }
}
