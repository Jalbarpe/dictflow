from AppKit import NSWorkspace
from config import APP_CONTEXTS


def get_active_app_bundle_id():
    """Get the bundle identifier of the currently active application."""
    active_app = NSWorkspace.sharedWorkspace().activeApplication()
    if active_app:
        return active_app.get("NSApplicationBundleIdentifier", "")
    return ""


def get_context():
    """Determine the context type based on the active application.

    Returns: "code", "chat", or "general"
    """
    bundle_id = get_active_app_bundle_id()

    for prefix, context in APP_CONTEXTS.items():
        if bundle_id.startswith(prefix):
            return context

    return "general"
