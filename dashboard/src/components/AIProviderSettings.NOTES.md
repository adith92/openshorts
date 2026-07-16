# AI Provider Settings behavior

The custom endpoint form:

- derives `BASE_URL/models` from the configured API root;
- authenticates discovery with `Authorization: Bearer API_KEY`;
- starts discovery after a short debounce;
- recognizes `data`, `models`, `result.data`, and `result.models` arrays;
- prioritizes model IDs containing `gemini`;
- provides a manual model-ID fallback;
- uses the selected ID unchanged for chat completions;
- never includes the API key in displayed error messages.

The direct Google Gemini API-key provider remains available only as a fallback for Gemini-specific Files API workflows.
