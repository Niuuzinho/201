package io.github.niuuzinho.caderno201;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // instalador interno de atualizações (window.AndroidUpdater na página)
        getBridge().getWebView().addJavascriptInterface(
                new AndroidUpdater(this, getBridge().getWebView()), "AndroidUpdater");
    }
}
