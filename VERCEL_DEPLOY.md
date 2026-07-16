# Deploy OpenShorts Frontend to Vercel

OpenShorts is deployed as a split architecture:

- **Vercel** serves the React/Vite dashboard.
- **Docker/EC2** continues to run FastAPI, FFmpeg processing, background jobs, local output files, Gemini CLI OAuth, and the Remotion renderer.

The repository root contains `vercel.json`, so the project can be imported without changing the Vercel Root Directory. Vercel runs:

```text
npm --prefix dashboard ci
npm --prefix dashboard run build
```

and publishes:

```text
dashboard/dist
```

## Temporary upstream proxy

The Vercel deployment proxies these paths to the existing OpenShorts server:

- `/api/*`
- `/videos/*`
- `/thumbnails/*`
- `/gallery/*`
- `/video/*`
- `/render/*`

The temporary upstream is:

```text
https://www.openshorts.app
```

Do not point `www.openshorts.app` to Vercel while it is also used as the upstream, because that would create a rewrite loop.

Before moving the primary domain to Vercel, create a dedicated backend hostname such as:

```text
api.openshorts.app
```

Point that hostname to the EC2/Nginx server, enable HTTPS, and replace the rewrite destinations in `vercel.json`.

## Deploy

1. Import `adith92/openshorts` into Vercel.
2. Keep the project root at the repository root.
3. Vercel reads the build settings from `vercel.json`.
4. Deploy first on the generated `*.vercel.app` preview URL.
5. Test dashboard loading, `/api/config`, uploads, job status polling, video playback, thumbnails, gallery, and rendering.
6. Only move the production domain after the dedicated backend hostname is working.

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

A future cloud-native migration would move jobs to a durable queue, artifacts to object storage, processing to workers/containers, and state to a database.
