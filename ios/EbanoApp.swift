import SwiftUI
import UIKit
import WebKit
import CoreHaptics
import AVFAudio

@main
struct EbanoApp: App {
    var body: some Scene {
        WindowGroup {
            InstrumentView().ignoresSafeArea().preferredColorScheme(.dark)
                .statusBarHidden(true)
        }
    }
}

struct InstrumentView: UIViewRepresentable {
    func makeCoordinator() -> Coordinator { Coordinator() }
    func makeUIView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        config.allowsInlineMediaPlayback = true
        config.mediaTypesRequiringUserActionForPlayback = []
        let coordinator = context.coordinator
        let controller = config.userContentController
        let js = "window.__nativeHapticsSupported = \(coordinator.supported ? "true" : "false");"
        controller.addUserScript(WKUserScript(source: js, injectionTime: .atDocumentStart, forMainFrameOnly: true))
        controller.add(coordinator, name: "guitarHaptic")
        let view = WKWebView(frame: .zero, configuration: config)
        view.navigationDelegate = coordinator
        view.isOpaque = false
        view.backgroundColor = UIColor(red: 0.04, green: 0.03, blue: 0.025, alpha: 1)
        view.scrollView.isScrollEnabled = false
        view.scrollView.bounces = false
        view.scrollView.contentInsetAdjustmentBehavior = .never
        view.allowsBackForwardNavigationGestures = false
        view.scrollView.panGestureRecognizer.isEnabled = false
        view.scrollView.pinchGestureRecognizer?.isEnabled = false
        view.isMultipleTouchEnabled = true
        coordinator.prepare()
        if let url = Bundle.main.url(forResource: "index", withExtension: "html") {
            view.loadFileURL(url, allowingReadAccessTo: url.deletingLastPathComponent())
        } else {
            view.loadHTMLString("<meta name='viewport' content='width=device-width'><body style='background:#15110e;color:#f7dfbd;font:18px system-ui;padding:2em'>Falta el recurso index.html en el bundle.</body>", baseURL: nil)
        }
        return view
    }
    func updateUIView(_ view: WKWebView, context: Context) {}
    static func dismantleUIView(_ view: WKWebView, coordinator: Coordinator) {
        view.configuration.userContentController.removeScriptMessageHandler(forName: "guitarHaptic")
        coordinator.shutdown()
    }

    final class Coordinator: NSObject, WKScriptMessageHandler, WKNavigationDelegate {
        let supported = CHHapticEngine.capabilitiesForHardware().supportsHaptics
        private var engine: CHHapticEngine?
        private var lastPulse: TimeInterval = 0
        private var prepared = false
        private var observers = [NSObjectProtocol]()
        private let allowedKinds: Set<String> = ["pick", "fret", "slide", "bend", "hammer", "pull"]

        func prepare() {
            guard !prepared else { return }
            prepared = true
            do {
                let session = AVAudioSession.sharedInstance()
                try session.setCategory(.playback, mode: .default, options: [.mixWithOthers])
                try session.setActive(true)
            } catch { print("Audio session: \(error)") }
            guard supported else { return }
            let center = NotificationCenter.default
            observers.append(center.addObserver(forName: UIApplication.didBecomeActiveNotification, object: nil, queue: .main) { [weak self] _ in self?.start() })
            observers.append(center.addObserver(forName: UIApplication.willResignActiveNotification, object: nil, queue: .main) { [weak self] _ in self?.engine?.stop(completionHandler: nil) })
            start()
        }
        private func start() {
            guard supported else { return }
            do {
                if engine == nil {
                    let e = try CHHapticEngine()
                    e.playsHapticsOnly = true
                    e.isAutoShutdownEnabled = true
                    e.resetHandler = { [weak self] in DispatchQueue.main.async { self?.start() } }
                    e.stoppedHandler = { _ in }
                    engine = e
                }
                try engine?.start()
            } catch { print("Core Haptics: \(error)") }
        }
        func userContentController(_ userContentController: WKUserContentController, didReceive message: WKScriptMessage) {
            guard supported, message.name == "guitarHaptic", message.frameInfo.isMainFrame,
                  let value = message.body as? [String: Any], let kind = value["kind"] as? String,
                  allowedKinds.contains(kind), let rawIntensity = value["intensity"] as? NSNumber,
                  let rawSharpness = value["sharpness"] as? NSNumber,
                  rawIntensity.doubleValue.isFinite, rawSharpness.doubleValue.isFinite else { return }
            let now = ProcessInfo.processInfo.systemUptime
            guard now - lastPulse >= 0.012 else { return }
            lastPulse = now
            let intensity = Float(max(0.05, min(1, rawIntensity.doubleValue)))
            let sharpness = Float(max(0.05, min(1, rawSharpness.doubleValue)))
            do {
                if engine == nil { start() }
                guard let e = engine else { return }
                let event = CHHapticEvent(eventType: .hapticTransient, parameters: [
                    CHHapticEventParameter(parameterID: .hapticIntensity, value: intensity),
                    CHHapticEventParameter(parameterID: .hapticSharpness, value: sharpness)
                ], relativeTime: 0)
                let pattern = try CHHapticPattern(events: [event], parameters: [])
                let player = try e.makePlayer(with: pattern)
                do { try player.start(atTime: CHHapticTimeImmediate) }
                catch { try e.start(); try player.start(atTime: CHHapticTimeImmediate) }
            } catch { print("Haptic event: \(error)") }
        }
        func webView(_ webView: WKWebView, decidePolicyFor navigationAction: WKNavigationAction, decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            let url = navigationAction.request.url
            decisionHandler(url?.isFileURL == true || url?.scheme == "about" ? .allow : .cancel)
        }
        func shutdown() {
            for observer in observers { NotificationCenter.default.removeObserver(observer) }
            observers.removeAll()
            engine?.stop(completionHandler: nil)
            engine = nil
            prepared = false
        }
    }
}
