import re

VIDEO_LINK_REGEX = re.compile(
    r'.*?'
    r'https?://(?:www\.)?'
    r'(?:youtube\.com/(?:watch\?v=|shorts/)|youtu\.be/|instagram\.com/reel/)'
    r'[^\s<>"\']+',
    re.IGNORECASE
)


def get_video_link_from_text(text: str) -> str:
    match = VIDEO_LINK_REGEX.search(text)
    return match.group() if match else ""


def is_valid_mac_address(mac: str) -> bool:
    patterns = [
        r'^[0-9A-Fa-f]{2}[:-]{1}[0-9A-Fa-f]{2}[:-]{1}[0-9A-Fa-f]{2}[:-]{1}[0-9A-Fa-f]{2}[:-]{1}[0-9A-Fa-f]{2}[:-]{1}[0-9A-Fa-f]{2}$',
        r'^[0-9A-Fa-f]{12}$',
        r'^[0-9A-Fa-f]{2}\.[0-9A-Fa-f]{2}\.[0-9A-Fa-f]{2}\.[0-9A-Fa-f]{2}\.[0-9A-Fa-f]{2}\.[0-9A-Fa-f]{2}$',
    ]
    return any(re.match(pattern, mac) for pattern in patterns)
