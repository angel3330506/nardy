package am.nardy.ads;

import android.os.Handler;
import android.os.Looper;
import com.getcapacitor.JSObject;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.yandex.mobile.ads.common.AdError;
import com.yandex.mobile.ads.common.AdRequest;
import com.yandex.mobile.ads.common.AdRequestError;
import com.yandex.mobile.ads.common.ImpressionData;
import com.yandex.mobile.ads.interstitial.InterstitialAd;
import com.yandex.mobile.ads.interstitial.InterstitialAdEventListener;
import com.yandex.mobile.ads.interstitial.InterstitialAdLoadListener;
import com.yandex.mobile.ads.interstitial.InterstitialAdLoader;
import com.yandex.mobile.ads.rewarded.Reward;
import com.yandex.mobile.ads.rewarded.RewardedAd;
import com.yandex.mobile.ads.rewarded.RewardedAdEventListener;
import com.yandex.mobile.ads.rewarded.RewardedAdLoadListener;
import com.yandex.mobile.ads.rewarded.RewardedAdLoader;

// Реклама Яндекса (Yandex Mobile Ads 8): полноэкранная между партиями и ролик за награду.
// ID блоков приходят из игры (configure); пока своих нет — тестовые блоки Яндекса demo-*.
@CapacitorPlugin(name = "NardyAds")
public class NardyAdsPlugin extends Plugin {
    private String interId = "demo-interstitial-yandex", rewId = "demo-rewarded-yandex";
    private InterstitialAd inter; private RewardedAd rew;
    private boolean loadingI, loadingR;
    private final Handler main = new Handler(Looper.getMainLooper());

    @PluginMethod
    public void configure(PluginCall call) {
        String i = call.getString("interstitial"), r = call.getString("rewarded");
        if (i != null && !i.isEmpty()) interId = i;
        if (r != null && !r.isEmpty()) rewId = r;
        loadInter(); loadRew();
        call.resolve();
    }

    @PluginMethod
    public void isReady(PluginCall call) {
        JSObject o = new JSObject(); o.put("interstitial", inter != null); o.put("rewarded", rew != null); call.resolve(o);
    }

    private void loadInter() {
        if (inter != null || loadingI) return; loadingI = true;
        main.post(() -> new InterstitialAdLoader(getContext()).loadAd(new AdRequest.Builder(interId).build(), new InterstitialAdLoadListener() {
            @Override public void onAdLoaded(InterstitialAd ad) { inter = ad; loadingI = false; }
            @Override public void onAdFailedToLoad(AdRequestError e) { loadingI = false; main.postDelayed(() -> loadInter(), 60000); }
        }));
    }

    private void loadRew() {
        if (rew != null || loadingR) return; loadingR = true;
        main.post(() -> new RewardedAdLoader(getContext()).loadAd(new AdRequest.Builder(rewId).build(), new RewardedAdLoadListener() {
            @Override public void onAdLoaded(RewardedAd ad) { rew = ad; loadingR = false; }
            @Override public void onAdFailedToLoad(AdRequestError e) { loadingR = false; main.postDelayed(() -> loadRew(), 60000); }
        }));
    }

    @PluginMethod
    public void showInterstitial(PluginCall call) {
        final InterstitialAd ad = inter;
        if (ad == null) { loadInter(); JSObject o = new JSObject(); o.put("shown", false); call.resolve(o); return; }
        inter = null;
        ad.setAdEventListener(new InterstitialAdEventListener() {
            boolean done = false;
            private void finish(boolean shown) { if (done) return; done = true; JSObject o = new JSObject(); o.put("shown", shown); call.resolve(o); loadInter(); }
            @Override public void onAdShown() {}
            @Override public void onAdFailedToShow(AdError e) { finish(false); }
            @Override public void onAdDismissed() { finish(true); }
            @Override public void onAdClicked() {}
            @Override public void onAdImpression(ImpressionData d) {}
        });
        main.post(() -> ad.show(getActivity()));
    }

    @PluginMethod
    public void showRewarded(PluginCall call) {
        final RewardedAd ad = rew;
        if (ad == null) { loadRew(); JSObject o = new JSObject(); o.put("shown", false); o.put("rewarded", false); call.resolve(o); return; }
        rew = null;
        ad.setAdEventListener(new RewardedAdEventListener() {
            boolean done = false, got = false;
            private void finish(boolean shown) { if (done) return; done = true; JSObject o = new JSObject(); o.put("shown", shown); o.put("rewarded", got); call.resolve(o); loadRew(); }
            @Override public void onAdShown() {}
            @Override public void onAdFailedToShow(AdError e) { finish(false); }
            @Override public void onAdDismissed() { finish(true); }
            @Override public void onAdClicked() {}
            @Override public void onAdImpression(ImpressionData d) {}
            @Override public void onRewarded(Reward r) { got = true; }
        });
        main.post(() -> ad.show(getActivity()));
    }
}
