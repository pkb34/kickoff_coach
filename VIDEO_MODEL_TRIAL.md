# Direct video-model trial (v8)

The welcome page currently keeps the full-body still cover. No generated video is used in this version.

On 2026-09-20, a single image-to-video request was sent to Google's `gemini-omni-1.1-flash` model through the project's configured Gemini API key. The source illustration was used as a visual reference; no still frames were assembled into a video. The API rejected the request before generation with HTTP 429:

> Rate limit exceeded for model gemini-omni-1.1-flash (limit: 0 requests per day on Free Tier).

No video was returned. A paid-tier Gemini API project is required for this model. According to the official pricing page checked on 2026-09-20, Gemini Omni Flash has no free API tier and costs approximately USD 0.10 per second of 720p video on the standard paid tier. A paid key would allow a genuine model-generated trial, but the result would still need visual review before replacing the cover.

Model documentation: https://ai.google.dev/gemini-api/docs/omni

Pricing: https://ai.google.dev/gemini-api/docs/pricing
