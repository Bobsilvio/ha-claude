"""Image handling and formatting helpers for different AI providers."""


def parse_image_data(data_uri: str) -> tuple:
    """
    Parse data URI to extract media type and base64 data.
    Example: 'data:image/jpeg;base64,/9j/4AAQ...' -> ('image/jpeg', '/9j/4AAQ...')
    """
    if not data_uri or not data_uri.startswith('data:'):
        return None, None

    try:
        # Format: data:image/jpeg;base64,<base64_data>
        header, data = data_uri.split(',', 1)
        media_type = header.split(';')[0].split(':')[1]
        return media_type, data
    except:
        return None, None


def format_message_with_image_anthropic(text: str, media_type: str, base64_data: str) -> list:
    """
    Format message with image for Anthropic Claude.
    Returns content array with text and image blocks.
    """
    return [
        {"type": "text", "text": text},
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": base64_data
            }
        }
    ]


def format_message_with_image_openai(text: str, data_uri: str) -> list:
    """
    Format message with image for OpenAI/GitHub.
    Returns content array with text and image_url blocks.
    """
    return [
        {"type": "text", "text": text},
        {
            "type": "image_url",
            "image_url": {"url": data_uri}
        }
    ]


def format_message_with_image_google(text: str, media_type: str, base64_data: str) -> list:
    """
    Format message with image for Google Gemini.
    Returns parts array for Gemini format.
    """
    # Gemini uses inline_data format
    return [
        {"text": text},
        {
            "inline_data": {
                "mime_type": media_type,
                "data": base64_data
            }
        }
    ]
