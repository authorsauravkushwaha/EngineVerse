# Android: PWA and signed APK

The full EngineVerse website is usable on an Android phone **without an APK**:
open its HTTPS origin in Chrome, then use **Install app / Add to Home screen**.
`GET /install` has instructions and is public even if the catalogue requires
sign-in. The browser/PWA uses the same account and private server database as a
desktop browser; it is not a second site. Only previously cached *public* pages
may work offline. Sign-in, saved practice and code judging require a connection.

An APK is optional. This repository can build a **Trusted Web Activity (TWA)**
which opens that *hosted full app*, **not** the GitHub Pages reading copy. An APK
cannot run PostgreSQL, a Python API or Judge0 on a phone. It does not make
backend-disabled operations available. A GitHub Release is not a Play Store
listing, and this repository has no published or approved Android package yet.

## Required HTTPS site and Digital Asset Links

Deploy the FastAPI app on a public HTTPS origin first (see
[Deployment](DEPLOYMENT.md#public-https-edge-one-operator-installation-not-one-per-learner)).
It serves `/manifest.webmanifest`, `/sw.js`, icons under `/static/icons/`, and
`/.well-known/assetlinks.json`. The last route returns **404** until the web
process receives both:

- `ENGINEVERSE_TWA_PACKAGE`: one stable lowercase Android package name,
  e.g. `org.example.engineverse`. It must not change between updates.
- `ENGINEVERSE_TWA_SHA256`: colon-separated SHA-256 fingerprint of the **actual
  signing certificate** (32 hex byte pairs). Do not substitute an upload key or
  a debug certificate if it is not the key used to sign the downloadable APK.

`deploy/docker-compose.yml` forwards both variables from the ignored
`deploy/.env` to the web container. After setting them, restart web, verify
`https://YOUR_HOST/.well-known/assetlinks.json` returns the right package and
fingerprint, and run:

```bash
python scripts/verify_twa.py --url https://YOUR_HOST \
  --package org.example.engineverse --fingerprint 'AA:BB:...'
```

Invalid values are not echoed by the server. Digital Asset Links only proves
that your domain recognizes a certificate; test the actual APK on an Android
device as well. On an unverified origin, Android may fall back to a browser tab
rather than a trusted full-screen experience.

## Build and publish a signed APK

1. **Create and back up a keystore outside the repository.** For example on a
   trusted computer with a JDK, use `keytool -genkeypair -keystore
   /secure/offline/engineverse.jks -alias engineverse -keyalg RSA -keysize 3072
   -validity 10000` and enter passwords interactively. Get its SHA-256 via
   `keytool -list -v -keystore /secure/offline/engineverse.jks -alias engineverse`;
   keytool prompts for the password. Never commit or paste the key, passwords or
   a base64 copy into chat/PRs/logs. Keep an offline recovery copy: without the
   **same** signing key you cannot ship an update over an existing install.
2. Configure the full site and Digital Asset Links as above. In the repository
   GitHub **Actions variables**, set `ENGINEVERSE_APP_URL` (the exact full HTTPS
   origin), `ENGINEVERSE_TWA_PACKAGE` and `ENGINEVERSE_TWA_ALIAS`. Upload the
   base64 keystore as the **secret** `ANDROID_KEYSTORE_BASE64` and its two
   passwords as **secrets** `ANDROID_KEYSTORE_PASSWORD` and
   `ANDROID_KEY_PASSWORD`. Limit who can trigger releases and protect the
   `android-release` environment in GitHub settings. These are *build* secrets,
   never frontend variables and never files in this repository.
3. After the hosting and signing settings are live, manually dispatch **Signed
   Android APK** on `main` with a version such as `v1.0.0`. The workflow pins
   Bubblewrap dependencies via `android/package-lock.json`, builds from the
   hosted manifest, checks `/health`/registration/install, compares Digital
   Asset Links with the keystore **before** building, verifies the built APK
   signature, and publishes only `EngineVerse.apk` and its SHA-256 checksum in
   release `android-v1.0.0`. Its Android `versionCode` comes from the monotonic
   workflow run number. Releasing another version needs a new tag and the same
   package/key. **This workspace cannot build or test the APK without a live
   HTTPS host, Android SDK and operator-provided signing key.**
4. Only when the release exists, put this exact URL in both the ignored server
   `deploy/.env` (`ENGINEVERSE_APK_URL`) and the repository Actions **variable**
   of the same name:

   ```text
   https://github.com/authorsauravkushwaha/EngineVerse/releases/download/android-v1.0.0/EngineVerse.apk
   ```

   Restart web so `/install` offers the direct download. The next `main` Pages
   workflow verifies the Release asset exists and is not a draft before showing
   the same link on the gateway. With no configured URL, neither site pretends
   that an APK exists. The server validates that links point to a versioned
   EngineVerse GitHub Release, not a caller-supplied APK mirror.

Android may ask to allow installation from your browser. Compare the downloaded
file's SHA-256 to the accompanying `EngineVerse.apk.sha256` and install **only**
from the official release. Updates require downloading a new signed release
(or using the browser/PWA, which updates with the website). Never publish a
random unsigned or debug-signed APK as if it were the release.

For a local developer-owned TWA build instead of this manual release workflow,
Bubblewrap's `init --manifest https://YOUR_HOST/manifest.webmanifest` and `build`
can be used after hosting. Its interactive signing setup and generated Android
project are local artifacts, not source files or backend services. The web
manifest's root scope must remain on the same origin as Digital Asset Links.

## Listing pack and limitations

`python scripts/prepare_listing.py --site-name "$SITE_NAME"` creates
`android/listing/`: text, the existing 512 icon and a feature graphic. It is a
draft, not a store submission and not Play approval. No university or SK
Nexora endorsement is claimed. Core learning stays free; certificates are
platform records, not accredited qualifications. Play submission/review, an
isolated judge and an actual public backend are separate operator tasks.
