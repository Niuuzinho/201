package io.github.niuuzinho.caderno201;

import android.app.Activity;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageInstaller;
import android.net.Uri;
import android.os.Build;
import android.provider.Settings;
import android.webkit.JavascriptInterface;
import android.webkit.WebView;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.io.OutputStream;
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

    private static final String ACTION = "io.github.niuuzinho.caderno201.INSTALL_RESULT";

    public AndroidUpdater(Activity activity, WebView web) {
        this.activity = activity;
        this.web = web;
        BroadcastReceiver receiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                onInstallResult(intent);
            }
        };
        IntentFilter filter = new IntentFilter(ACTION);
        if (Build.VERSION.SDK_INT >= 33) {
            activity.registerReceiver(receiver, filter, Context.RECEIVER_NOT_EXPORTED);
        } else {
            activity.registerReceiver(receiver, filter);
        }
    }

    /** Resposta do instalador do Android: pede confirmação, conclui ou explica por que recusou. */
    private void onInstallResult(Intent intent) {
        int status = intent.getIntExtra(PackageInstaller.EXTRA_STATUS, -1);
        String msg = intent.getStringExtra(PackageInstaller.EXTRA_STATUS_MESSAGE);
        if (status == PackageInstaller.STATUS_PENDING_USER_ACTION) {
            Intent confirm = intent.getParcelableExtra(Intent.EXTRA_INTENT);
            if (confirm != null) {
                confirm.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                activity.startActivity(confirm);
                emit("done", "", 100);
            } else {
                emit("error", "O Android não abriu a janela de confirmação.", -1);
            }
        } else if (status == PackageInstaller.STATUS_SUCCESS) {
            emit("done", "", 100);
        } else {
            emit("error", "O Android recusou a instalação (código " + status + "): " + (msg != null ? msg : "sem detalhes"), -1);
        }
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

        // confere que é mesmo um APK (arquivo zip começa com "PK")
        InputStream chk = new FileInputStream(apk);
        int b0 = chk.read(), b1 = chk.read();
        chk.close();
        if (b0 != 'P' || b1 != 'K') throw new Exception("O arquivo baixado não é um APK válido (" + apk.length() + " bytes).");

        // entrega o arquivo ao instalador do Android por sessão (sem URI de arquivo)
        PackageInstaller installer = activity.getPackageManager().getPackageInstaller();
        PackageInstaller.SessionParams params =
                new PackageInstaller.SessionParams(PackageInstaller.SessionParams.MODE_FULL_INSTALL);
        int sessionId = installer.createSession(params);
        PackageInstaller.Session session = installer.openSession(sessionId);
        try {
            InputStream src = new FileInputStream(apk);
            OutputStream dst = session.openWrite("Caderno201.apk", 0, apk.length());
            byte[] chunk = new byte[65536];
            int r;
            while ((r = src.read(chunk)) != -1) dst.write(chunk, 0, r);
            session.fsync(dst);
            dst.close();
            src.close();
            Intent result = new Intent(ACTION).setPackage(activity.getPackageName());
            int flags = PendingIntent.FLAG_UPDATE_CURRENT;
            if (Build.VERSION.SDK_INT >= 31) flags |= PendingIntent.FLAG_MUTABLE;
            PendingIntent pending = PendingIntent.getBroadcast(activity, sessionId, result, flags);
            session.commit(pending.getIntentSender());
        } finally {
            session.close();
        }
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
