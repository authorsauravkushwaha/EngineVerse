#!/usr/bin/env python3
"""Build and sign the standalone EngineVerse Android APK (`EngineVerse.apk`).

Produces a signed, installable Android package (`io.github.authorsauravkushwaha.engineverse`)
that runs EngineVerse on an Android phone with WebView DOMStorage, IndexedDB,
Service Worker caching, offline fallback, hardware Back navigation, and GitHub
learner progress sync.

Works with either the public GitHub Pages site
(`https://authorsauravkushwaha.github.io/EngineVerse/`) or a custom HTTPS
`ENGINEVERSE_APP_URL`.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_START_URL = "https://authorsauravkushwaha.github.io/EngineVerse/"
DEFAULT_PACKAGE = "io.github.authorsauravkushwaha.engineverse"
DEFAULT_VERSION = "v1.0.0"

_PACKAGE_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+\Z")
_VERSION_RE = re.compile(r"^v([0-9]+)\.([0-9]+)\.([0-9]+)\Z")


def normalise_start_url(url: str | None) -> str:
    raw = (url or "").strip()
    if not raw:
        return DEFAULT_START_URL
    parts = urlsplit(raw)
    if parts.scheme != "https" or not parts.hostname or "." not in parts.hostname:
        raise ValueError("Android start URL must be a public HTTPS URL.")
    if parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("Android start URL must not include credentials, query or fragment.")
    path = parts.path or "/"
    if not path.endswith("/"):
        path += "/"
    return f"https://{parts.hostname}{path}"


def validate_config(
    start_url: str = DEFAULT_START_URL,
    package: str = DEFAULT_PACKAGE,
    version: str = DEFAULT_VERSION,
    version_code: int = 100,
) -> dict[str, str | int]:
    clean_url = normalise_start_url(start_url)
    pkg = (package or DEFAULT_PACKAGE).strip()
    if not _PACKAGE_RE.fullmatch(pkg):
        raise ValueError("Invalid Android package name.")
    ver = (version or DEFAULT_VERSION).strip()
    match = _VERSION_RE.fullmatch(ver)
    if not match:
        raise ValueError("Version must be vMAJOR.MINOR.PATCH (e.g. v1.0.0).")
    if not (1 <= int(version_code) <= 2_100_000_000):
        raise ValueError("version_code must be a positive integer.")
    parts = urlsplit(clean_url)
    return {
        "start_url": clean_url,
        "host": parts.hostname or "authorsauravkushwaha.github.io",
        "path_prefix": parts.path or "/EngineVerse/",
        "package": pkg,
        "version": ver,
        "version_name": ver[1:],
        "version_code": int(version_code),
    }


def generate_manifest(cfg: dict[str, str | int]) -> str:
    pkg = cfg["package"]
    vcode = cfg["version_code"]
    vname = cfg["version_name"]
    host = cfg["host"]
    path_prefix = cfg["path_prefix"]
    return f"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{pkg}"
    android:versionCode="{vcode}"
    android:versionName="{vname}">

    <uses-sdk android:minSdkVersion="24" android:targetSdkVersion="34" />
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

    <application
        android:label="EngineVerse"
        android:icon="@mipmap/ic_launcher"
        android:usesCleartextTraffic="false"
        android:allowBackup="true"
        android:hardwareAccelerated="true"
        android:theme="@android:style/Theme.DeviceDefault.NoActionBar">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:launchMode="singleTask"
            android:configChanges="orientation|screenSize|screenLayout|keyboardHidden|uiMode">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
            <intent-filter android:autoVerify="true">
                <action android:name="android.intent.action.VIEW" />
                <category android:name="android.intent.category.DEFAULT" />
                <category android:name="android.intent.category.BROWSABLE" />
                <data android:scheme="https" android:host="{host}" android:pathPrefix="{path_prefix}" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""


def generate_main_activity(cfg: dict[str, str | int]) -> str:
    pkg = cfg["package"]
    start_url = cfg["start_url"]
    host = cfg["host"]
    return f"""package {pkg};

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.net.Uri;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.webkit.CookieManager;
import android.webkit.DownloadListener;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.ProgressBar;

public class MainActivity extends Activity {{
    private static final String START_URL = "{start_url}";
    private static final String ALLOWED_HOST = "{host}";
    private WebView webView;
    private ProgressBar progressBar;

    @Override
    protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        requestWindowFeature(Window.FEATURE_NO_TITLE);

        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.parseColor("#181f2c"));

        webView = new WebView(this);
        progressBar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progressBar.setMax(100);
        FrameLayout.LayoutParams pbParams = new FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, 8
        );

        root.addView(webView, new FrameLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT,
            ViewGroup.LayoutParams.MATCH_PARENT
        ));
        root.addView(progressBar, pbParams);
        setContentView(root);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setSupportZoom(true);
        settings.setBuiltInZoomControls(true);
        settings.setDisplayZoomControls(false);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setUserAgentString(settings.getUserAgentString() + " EngineVerseAndroid/1.0");
        settings.setCacheMode(isOnline() ? WebSettings.LOAD_DEFAULT : WebSettings.LOAD_CACHE_ELSE_NETWORK);

        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, false);

        webView.setWebChromeClient(new WebChromeClient() {{
            @Override
            public void onProgressChanged(WebView view, int newProgress) {{
                if (newProgress < 100) {{
                    progressBar.setVisibility(View.VISIBLE);
                    progressBar.setProgress(newProgress);
                }} else {{
                    progressBar.setVisibility(View.GONE);
                }}
            }}
        }});

        webView.setWebViewClient(new WebViewClient() {{
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {{
                Uri uri = request.getUrl();
                if (uri == null) return false;
                String scheme = uri.getScheme() != null ? uri.getScheme().toLowerCase() : "";
                String h = uri.getHost() != null ? uri.getHost().toLowerCase() : "";
                if ("https".equals(scheme) && (ALLOWED_HOST.equalsIgnoreCase(h) || "github.com".equalsIgnoreCase(h))) {{
                    if ("github.com".equalsIgnoreCase(h)) {{
                        startActivity(new Intent(Intent.ACTION_VIEW, uri));
                        return true;
                    }}
                    return false;
                }}
                if ("http".equals(scheme) || "https".equals(scheme) || "mailto".equals(scheme)) {{
                    startActivity(new Intent(Intent.ACTION_VIEW, uri));
                    return true;
                }}
                return true;
            }}

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {{
                if (request.isForMainFrame()) {{
                    view.getSettings().setCacheMode(WebSettings.LOAD_CACHE_ELSE_NETWORK);
                }}
            }}
        }});

        webView.setDownloadListener(new DownloadListener() {{
            @Override
            public void onDownloadStart(String url, String userAgent, String contentDisposition, String mimetype, long contentLength) {{
                if (url != null && url.startsWith("https://")) {{
                    startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url)));
                }}
            }}
        }});

        String initialUrl = START_URL;
        Intent intent = getIntent();
        if (intent != null && Intent.ACTION_VIEW.equals(intent.getAction()) && intent.getData() != null) {{
            Uri data = intent.getData();
            if ("https".equalsIgnoreCase(data.getScheme()) && ALLOWED_HOST.equalsIgnoreCase(data.getHost())) {{
                initialUrl = data.toString();
            }}
        }}
        webView.loadUrl(initialUrl);
    }}

    private boolean isOnline() {{
        try {{
            ConnectivityManager cm = (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);
            if (cm == null) return true;
            NetworkInfo info = cm.getActiveNetworkInfo();
            return info != null && info.isConnected();
        }} catch (Exception e) {{
            return true;
        }}
    }}

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {{
        if (keyCode == KeyEvent.KEYCODE_BACK && webView != null && webView.canGoBack()) {{
            webView.goBack();
            return true;
        }}
        return super.onKeyDown(keyCode, event);
    }}
}}
"""


def _find_sdk_tools() -> tuple[Path, Path, Path, Path, Path]:
    sdk_root = None
    for env_name in ("ANDROID_HOME", "ANDROID_SDK_ROOT"):
        val = os.environ.get(env_name, "").strip()
        if val and Path(val).is_dir():
            sdk_root = Path(val)
            break
    if sdk_root is None:
        default_sdk = Path("/usr/local/lib/android/sdk")
        if default_sdk.is_dir():
            sdk_root = default_sdk
    if sdk_root is None:
        raise RuntimeError("Android SDK not found in ANDROID_HOME or /usr/local/lib/android/sdk.")

    build_tools_dirs = sorted((sdk_root / "build-tools").glob("*"), reverse=True)
    if not build_tools_dirs:
        raise RuntimeError("No Android build-tools found under " + str(sdk_root))
    bt = build_tools_dirs[0]

    platforms = sorted((sdk_root / "platforms").glob("android-*"), reverse=True)
    android_jar = next((p / "android.jar" for p in platforms if (p / "android.jar").is_file()), None)
    if android_jar is None:
        raise RuntimeError("No android.jar found under " + str(sdk_root / "platforms"))

    return bt / "aapt2", bt / "d8", bt / "zipalign", bt / "apksigner", android_jar


def build_apk(
    out_apk: Path,
    *,
    start_url: str = DEFAULT_START_URL,
    package: str = DEFAULT_PACKAGE,
    version: str = DEFAULT_VERSION,
    version_code: int = 100,
) -> Path:
    cfg = validate_config(start_url=start_url, package=package, version=version, version_code=version_code)
    aapt2, d8, zipalign, apksigner, android_jar = _find_sdk_tools()

    with tempfile.TemporaryDirectory() as tmp_str:
        tmp = Path(tmp_str)
        manifest_path = tmp / "AndroidManifest.xml"
        manifest_path.write_text(generate_manifest(cfg), encoding="utf-8")

        res_dir = tmp / "res"
        mipmap_dir = res_dir / "mipmap-xxhdpi"
        mipmap_dir.mkdir(parents=True)
        icon_src = ROOT / "backend" / "static" / "icons" / "icon-192.png"
        shutil.copy2(icon_src, mipmap_dir / "ic_launcher.png")

        pkg_path = Path(*str(cfg["package"]).split("."))
        src_dir = tmp / "src" / pkg_path
        src_dir.mkdir(parents=True)
        java_file = src_dir / "MainActivity.java"
        java_file.write_text(generate_main_activity(cfg), encoding="utf-8")

        compiled_res = tmp / "compiled_res.zip"
        subprocess.run([str(aapt2), "compile", "--dir", str(res_dir), "-o", str(compiled_res)], check=True)

        gen_src = tmp / "gen"
        gen_src.mkdir()
        unaligned_apk = tmp / "unaligned.apk"
        subprocess.run([
            str(aapt2), "link",
            "-o", str(unaligned_apk),
            "-I", str(android_jar),
            "--manifest", str(manifest_path),
            "--java", str(gen_src),
            str(compiled_res),
            "--auto-add-overlay",
        ], check=True)

        classes_dir = tmp / "classes"
        classes_dir.mkdir()
        java_sources = [str(java_file)] + [str(p) for p in gen_src.rglob("*.java")]
        subprocess.run([
            "javac", "-source", "1.8", "-target", "1.8",
            "-cp", str(android_jar),
            "-d", str(classes_dir),
            *java_sources,
        ], check=True)

        dex_dir = tmp / "dex"
        dex_dir.mkdir()
        class_files = [str(p) for p in classes_dir.rglob("*.class")]
        subprocess.run([
            str(d8), "--lib", str(android_jar), "--output", str(dex_dir), *class_files
        ], check=True)

        with zipfile.ZipFile(unaligned_apk, "a", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(dex_dir / "classes.dex", "classes.dex")

        aligned_apk = tmp / "aligned.apk"
        subprocess.run([str(zipalign), "-f", "-p", "4", str(unaligned_apk), str(aligned_apk)], check=True)

        keystore = tmp / "release.jks"
        ks_b64 = os.environ.get("ANDROID_KEYSTORE_BASE64", "").strip()
        ks_pass = os.environ.get("ANDROID_KEYSTORE_PASSWORD", "").strip() or "EngineVerseReleaseKey2026"
        key_pass = os.environ.get("ANDROID_KEY_PASSWORD", "").strip() or ks_pass
        alias = os.environ.get("ENGINEVERSE_TWA_ALIAS", "").strip() or "engineverse"

        if ks_b64:
            keystore.write_bytes(base64.b64decode(ks_b64))
        else:
            subprocess.run([
                "keytool", "-genkeypair", "-v",
                "-keystore", str(keystore),
                "-alias", alias,
                "-keyalg", "RSA", "-keysize", "2048", "-validity", "10000",
                "-storepass", ks_pass, "-keypass", key_pass,
                "-dname", "CN=EngineVerse, OU=Engineering, O=EngineVerse, L=Gaya, ST=Bihar, C=IN",
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        out_apk.parent.mkdir(parents=True, exist_ok=True)
        sign_env = {**os.environ, "EV_KS_PASS": ks_pass, "EV_KEY_PASS": key_pass}
        subprocess.run([
            str(apksigner), "sign",
            "--ks", str(keystore),
            "--ks-key-alias", alias,
            "--ks-pass", "env:EV_KS_PASS",
            "--key-pass", "env:EV_KEY_PASS",
            "--out", str(out_apk),
            str(aligned_apk),
        ], check=True, env=sign_env)

        subprocess.run([str(apksigner), "verify", "--verbose", str(out_apk)], check=True)

    digest = hashlib.sha256(out_apk.read_bytes()).hexdigest()
    sha_file = out_apk.with_name(out_apk.name + ".sha256")
    sha_file.write_text(f"{digest}  {out_apk.name}\n", encoding="utf-8")
    print(f"Built and verified signed APK: {out_apk} ({out_apk.stat().st_size} bytes, SHA-256: {digest})")
    return out_apk


def self_check() -> None:
    cfg = validate_config()
    assert cfg["start_url"] == "https://authorsauravkushwaha.github.io/EngineVerse/"
    assert cfg["package"] == DEFAULT_PACKAGE
    manifest = generate_manifest(cfg)
    assert 'android:name="android.permission.INTERNET"' in manifest
    assert 'android:host="authorsauravkushwaha.github.io"' in manifest
    java_code = generate_main_activity(cfg)
    assert "setJavaScriptEnabled(true)" in java_code
    assert "setDomStorageEnabled(true)" in java_code
    assert "KEYCODE_BACK" in java_code
    assert (ROOT / "backend" / "static" / "icons" / "icon-192.png").is_file()
    for bad_url in ("http://example.org", "https://localhost", "https://x.org?a=1"):
        try:
            normalise_start_url(bad_url)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Accepted invalid start URL: {bad_url}")
    print("Android APK builder self-check ok")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="dist/EngineVerse.apk", help="Output APK path")
    parser.add_argument("--url", default=os.environ.get("ENGINEVERSE_APP_URL", "") or DEFAULT_START_URL)
    parser.add_argument("--package", default=os.environ.get("ENGINEVERSE_TWA_PACKAGE", "") or DEFAULT_PACKAGE)
    parser.add_argument("--version", default=os.environ.get("APK_VERSION", "") or DEFAULT_VERSION)
    parser.add_argument("--version-code", type=int, default=int(os.environ.get("GITHUB_RUN_NUMBER", "100") or 100))
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args()

    if args.self_check:
        self_check()
        return 0

    build_apk(
        Path(args.out),
        start_url=args.url,
        package=args.package,
        version=args.version,
        version_code=args.version_code,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
