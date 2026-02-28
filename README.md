# chatKing

A LangBot plugin for generating chat ranking leaderboards with images.

## Features

- Generates ranking leaderboards based on chat activity
- Supports customizable time ranges (e.g., 1-day, 2-day rankings)
- Creates visual ranking images via API request
- Falls back to text-based rankings if image generation fails
- Easy configuration through plugin settings

## Installation

Install via the LangBot plugin marketplace


## Usage

### Command Format

To generate a ranking leaderboard, send a message in the format:

```
[number]日发言榜
```

Examples:
- `1日发言榜` - Generates a ranking for the current day
- `7日发言榜` - Generates a ranking for the past 7 days

### How It Works

1. The plugin monitors group messages and records chat activity
2. When a ranking command is received, it queries the database for chat statistics
3. It sends a request to the configured API to generate a ranking image
4. The generated image is sent back to the group
5. If image generation fails, a text-based ranking is sent instead

## Configuration

The plugin can be configured through the following settings:

| Setting | Description | Default Value |
|---------|-------------|---------------|
| `api_url` | API endpoint for generating ranking images | `contact author for free` |
| `access_token` | Access token for the API | `contact author for free` |

## Dependencies

- `requests` - For making API requests
- `langbot-plugin` - Base plugin framework

## License

[MIT](LICENSE)
