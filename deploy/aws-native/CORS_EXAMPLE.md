# CORS for automatic model discovery

The OpenShorts dashboard calls the custom endpoint's `GET /models` route directly.

Allow only the actual OpenShorts web origin, for example:

```text
https://openshorts.example.com
```

Required request methods and headers:

```text
GET
Authorization
Accept
```

Do not use a wildcard origin together with credentialed browser requests. Do not expose the custom endpoint without API authentication.

A generic response may include:

```http
Access-Control-Allow-Origin: https://openshorts.example.com
Access-Control-Allow-Methods: GET, OPTIONS
Access-Control-Allow-Headers: Authorization, Accept
Vary: Origin
```

The endpoint must also answer the browser's `OPTIONS` preflight when required.
