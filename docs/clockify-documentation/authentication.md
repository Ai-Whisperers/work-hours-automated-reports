# Authentication

## API Key Generation

1. Navigate to Profile Settings in Clockify
2. Generate API key
3. For subdomain workspaces (e.g., `subdomain.clockify.me`), generate workspace-specific key

## Usage

Add to request headers:

```
X-Api-Key: YOUR_API_KEY
```

or for addons:

```
X-Addon-Token: YOUR_ADDON_TOKEN
```

## Best Practices

- Generate unique keys per workspace
- Keep keys confidential
- Use workspace-specific keys for subdomain workspaces
- Rotate keys periodically

## Rate Limiting

- **Limit**: 50 requests/second per addon per workspace
- Exceeding limit returns HTTP 429
- Implement exponential backoff for retry logic
