# Deploy OpenShorts Frontend to Vercel

OpenShorts uses a split deployment architecture:

- **Vercel** serves the React/Vite dashboard.
- **Docker/EC2** runs FastAPI, FFmpeg processing, background jobs, generated media, Gemini CLI OAuth, and the Remotion renderer.

The repository root contains `vercel.json`, so the project can be imported without changing the Vercel Root Directory. Vercel runs:

```text
npm --prefix dashboard ci
npm --prefix dashboard run build
```

and publishes:

```text
dashboard/dist
```

## Backend hostname required

The Vercel frontend proxies these paths to the backend:

- `/api/*`
- `/videos/*`
- `/thumbnails/*`
- `/gallery/*`
- `/video/*`
- `/render/*`

The configured backend origin is:

```text
https://api.openshorts.app
```

Before the complete application can work:

1. Create the DNS record `api.openshorts.app` and point it to the EC2 server.
2. Keep ports `8000` and `3100` private where possible. Public traffic should enter through Nginx on ports `80` and `443`.
3. Enable HTTPS for `api.openshorts.app` using a valid certificate.
4. Confirm that `https://api.openshorts.app/api/config` returns JSON before testing the Vercel frontend.

Do not use `www.openshorts.app` as both the Vercel frontend domain and the rewrite destination. That configuration creates a routing loop.

## Deploy

1. Import `adith92/openshorts` into Vercel.
2. Keep the project root at the repository root.
3. Vercel reads its build settings from `vercel.json`.
4. Deploy first on the generated `*.vercel.app` URL.
5. Test dashboard loading and deep links.
6. Confirm `/api/config`, uploads, job status polling, video playback, thumbnails, gallery, and rendering.
7. Only move the production frontend domain after `api.openshorts.app` is healthy.

## What must remain outside Vercel

Do not deploy the current Python backend as Vercel Functions without a major redesign. It currently depends on:

- long-running background workers and in-memory queues;
- subprocess execution;
- FFmpeg and other system packages;
- large file uploads;
- writable local directories;
- generated media served from local storage;
- persistent Gemini CLI OAuth credentials;
- a separate Remotion rendering service.

A future cloud-native migration would move jobs to a durable queue, artifacts to object storage, processing to workers or containers, and state to a database.
