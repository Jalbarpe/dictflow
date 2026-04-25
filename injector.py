import time
import threading
from AppKit import NSPasteboard, NSPasteboardTypeString, NSStringPboardType
from Quartz import (
    CGEventCreateKeyboardEvent,
    CGEventSetFlags,
    CGEventPost,
    kCGHIDEventTap,
    kCGEventFlagMaskCommand,
)


def inject_text(text):
    """Inject text at the current cursor position via clipboard + Cmd+V.

    Preserves the original clipboard content and restores it after pasting.
    """
    if not text:
        return

    pasteboard = NSPasteboard.generalPasteboard()

    # Save current clipboard
    old_contents = pasteboard.stringForType_(NSPasteboardTypeString)

    # Set new text
    pasteboard.clearContents()
    pasteboard.setString_forType_(text, NSPasteboardTypeString)

    # Small delay to ensure clipboard is updated
    time.sleep(0.015)

    # Simulate Cmd+V
    _press_cmd_v()

    # Restore original clipboard after a delay (in background)
    def restore():
        time.sleep(1.0)
        pasteboard.clearContents()
        if old_contents:
            pasteboard.setString_forType_(old_contents, NSPasteboardTypeString)

    threading.Thread(target=restore, daemon=True).start()


def _press_cmd_v():
    """Simulate pressing Cmd+V using Quartz events."""
    # Key code 9 = 'v'
    v_key_code = 9

    # Key down with Cmd modifier
    event_down = CGEventCreateKeyboardEvent(None, v_key_code, True)
    CGEventSetFlags(event_down, kCGEventFlagMaskCommand)

    # Key up
    event_up = CGEventCreateKeyboardEvent(None, v_key_code, False)
    CGEventSetFlags(event_up, kCGEventFlagMaskCommand)

    CGEventPost(kCGHIDEventTap, event_down)
    CGEventPost(kCGHIDEventTap, event_up)
