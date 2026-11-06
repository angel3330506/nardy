import Foundation
import Capacitor
import AVFoundation
import UIKit

// Нативные мелочи «Нард»:
//  keepAwake({on}) — экран не гаснет, пока идёт партия;
//  звук игры не прерывает музыку/подкаст и молчит в беззвучном режиме (категория ambient);
//  setIcon({name}) / getIcon() — золотая и серебряная иконки за турниры двора.
@objc(NardyNativePlugin)
public class NardyNativePlugin: CAPPlugin, CAPBridgedPlugin {
    public let identifier = "NardyNativePlugin"
    public let jsName = "NardyNative"
    public let pluginMethods: [CAPPluginMethod] = [
        CAPPluginMethod(name: "keepAwake", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "setIcon", returnType: CAPPluginReturnPromise),
        CAPPluginMethod(name: "getIcon", returnType: CAPPluginReturnPromise)
    ]

    override public func load() {
        try? AVAudioSession.sharedInstance().setCategory(.ambient, mode: .default, options: [.mixWithOthers])
        try? AVAudioSession.sharedInstance().setActive(true)
    }

    @objc func keepAwake(_ call: CAPPluginCall) {
        let on = call.getBool("on") ?? true
        DispatchQueue.main.async {
            UIApplication.shared.isIdleTimerDisabled = on
            call.resolve()
        }
    }

    @objc func setIcon(_ call: CAPPluginCall) {
        let raw = call.getString("name") ?? ""
        let name: String? = raw.isEmpty ? nil : raw
        DispatchQueue.main.async {
            guard UIApplication.shared.supportsAlternateIcons else { call.reject("unsupported"); return }
            UIApplication.shared.setAlternateIconName(name) { error in
                if let e = error { call.reject(e.localizedDescription) } else { call.resolve() }
            }
        }
    }

    @objc func getIcon(_ call: CAPPluginCall) {
        DispatchQueue.main.async {
            call.resolve(["name": UIApplication.shared.alternateIconName ?? ""])
        }
    }
}
