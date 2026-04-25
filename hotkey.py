import threading
from Quartz import (
    CGEventTapCreate,
    CGEventTapEnable,
    CGEventGetIntegerValueField,
    CGEventGetFlags,
    CFMachPortCreateRunLoopSource,
    CFRunLoopAddSource,
    CFRunLoopGetCurrent,
    CFRunLoopRun,
    CFRunLoopStop,
    kCGSessionEventTap,
    kCGHeadInsertEventTap,
    kCGEventKeyDown,
    kCGEventKeyUp,
    kCGEventFlagsChanged,
    kCGKeyboardEventKeycode,
    kCFRunLoopDefaultMode,
)

# Flag mask for the Fn key (bit 23)
FN_FLAG_MASK = 0x800000
GLOBE_KEY_CODE = 63


class GlobeKeyListener:
    """Listens for Globe/Fn key press and release using CGEventTap."""

    def __init__(self, on_press=None, on_release=None):
        self._on_press = on_press
        self._on_release = on_release
        self._thread = None
        self._running = False
        self._run_loop = None
        self._fn_down = False

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._run_loop:
            CFRunLoopStop(self._run_loop)

    def _callback(self, proxy, event_type, event, refcon):
        if event_type == kCGEventFlagsChanged:
            key_code = CGEventGetIntegerValueField(event, kCGKeyboardEventKeycode)

            # Only react to keyCode 63 (the actual Globe/Fn key)
            if key_code != GLOBE_KEY_CODE:
                return event

            flags = CGEventGetFlags(event)
            fn_pressed = bool(flags & FN_FLAG_MASK)

            if fn_pressed and not self._fn_down:
                self._fn_down = True
                print("[DictFlow] Globe key DOWN")
                if self._on_press:
                    try:
                        self._on_press()
                    except Exception as e:
                        print(f"[DictFlow] on_press error: {e}")

            elif not fn_pressed and self._fn_down:
                self._fn_down = False
                print("[DictFlow] Globe key UP")
                if self._on_release:
                    try:
                        self._on_release()
                    except Exception as e:
                        print(f"[DictFlow] on_release error: {e}")

        return event

    def _run(self):
        event_mask = (1 << kCGEventKeyDown) | (1 << kCGEventKeyUp) | (1 << kCGEventFlagsChanged)

        tap = CGEventTapCreate(
            kCGSessionEventTap,
            kCGHeadInsertEventTap,
            0,
            event_mask,
            self._callback,
            None,
        )

        if tap is None:
            print(
                "[DictFlow] ERROR: No se pudo crear event tap.\n"
                "  System Settings > Privacy & Security > Accessibility"
            )
            return

        source = CFMachPortCreateRunLoopSource(None, tap, 0)
        self._run_loop = CFRunLoopGetCurrent()
        CFRunLoopAddSource(self._run_loop, source, kCFRunLoopDefaultMode)
        CGEventTapEnable(tap, True)

        print("[DictFlow] Globe key listener activo. Mantén fn para dictar.")
        CFRunLoopRun()
