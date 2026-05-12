from .calendar import GoogleCalendarSource
from .mail import GmailSource
from .health import AppleHealthSource
from .contacts import ContactsSource
from .photos import PhotosMetadataSource

__all__ = [
    "GoogleCalendarSource",
    "GmailSource",
    "AppleHealthSource",
    "ContactsSource",
    "PhotosMetadataSource",
]
