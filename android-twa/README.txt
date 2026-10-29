MockRep Android 1.0.6 source (premium-ready: billing permission added, inert while BILLING_ENABLED off)
Package com.ranjitsahoo.mockrep, versionCode 7, min Android 23, target Android 36.
Chrome Trusted Web Activity of https://mockrep.onrender.com/; launch link now /#sessions.
Uses browser site data, voice recognition, uploads and download behavior. No bundled website or WebView.
Build: Java 17, Android SDK 36/build-tools 36.0.0, Gradle 8.11.1, AGP 8.9.1.
Set local.properties sdk.dir to your Android SDK; set MOCKREP_KEYSTORE and MOCKREP_PASSWORD_FILE to private files. Alias mockrep. Never commit key/password.
IMPORTANT: original signing key matches 1.0.4, certificate SHA256 73D6AAAD49891BFE845A9FAF0F9BDDCA7F7A24D6A524484EA68ED1D1D6B50270.
The separately stored v2 key has a DIFFERENT certificate and is not compatible with 1.0.4. Do not use it for an in-place update.
Build/lint and signature checks pass. Browser cache migration and offline Practice Sessions tests pass.
Actual Android runtime install/update test could not run on the available single-core host. Physical phone microphone permission and real voice transcription still require testing. Do not call them verified.
No Play Store publication. No data deletion or uninstall required by the update design.
