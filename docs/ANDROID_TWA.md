# Android Trusted Web Activity

This wraps the site you already serve. It does not add a second application,
and it is not a Play Store submission. No listing has been created from this
repository. Play review, if you start one later, is a separate process with
its own outcome. Do not describe a listing as approved.

## What the site already serves

- `GET /manifest.webmanifest` from the origin root
- `GET /sw.js` from the origin root, with `Service-Worker-Allowed: /`
- Icons under `/static/icons/`

Those routes are the PWA. A Trusted Web Activity needs them on the public
HTTPS origin, not on a file URL and not on plain HTTP.

## Asset links

Bubblewrap checks `https://YOUR_HOST/.well-known/assetlinks.json`. The route
returns 404 until both of these are set in the web process environment:

- `ENGINEVERSE_TWA_PACKAGE` — a Java package name, such as `org.example.engineverse`
- `ENGINEVERSE_TWA_SHA256` — the SHA-256 of the signing certificate, colon-separated hex

An invalid value is also a 404, and the response does not echo it. Generate
the fingerprint from the certificate you sign with. Do not commit that
certificate, its keystore, or its password. `.gitignore` ignores `*.keystore`,
`*.jks` and `*.p12`.

## Bubblewrap

Bubblewrap is a local JDK tool. It is not a dependency of the web app and it
is not loaded from a CDN. Install it on the machine that builds the Android
package, not in the web image.

The usual sequence, after the site is actually served over HTTPS:

```bash
bubblewrap init --manifest https://YOUR_HOST/manifest.webmanifest
bubblewrap build
```

`init` asks for the keystore path. Keep that path outside the repository.
The fingerprint Bubblewrap prints is the value for `ENGINEVERSE_TWA_SHA256`.
Restart the web process so asset links are served, then:

```bash
bubblewrap validate --manifest https://YOUR_HOST/manifest.webmanifest
```

`validate` succeeding means Digital Asset Links match that certificate. It
does not mean Google Play has accepted the package.

## Listing pack

`python scripts/prepare_listing.py --site-name "$SITE_NAME"` writes
`android/listing/`. The committed pack uses the default name, EngineVerse.
Regenerate it when the configured name changes. The pack is text, the existing
512 icon, and a 1024×500 feature graphic. It is not a submission, it contains
no screenshots taken from a browser, and it does not say the listing is approved.

## What not to claim

- Do not claim the package is published.
- Do not claim a university or SK Nexora has approved a store listing.
- Do not embed a signing key to make the build easier.
- Core learning stays free. A store listing must not put the notes behind a
  purchase, and certificates must not be described as accredited degrees.
