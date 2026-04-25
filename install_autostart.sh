#!/bin/bash
# Install DictFlow as a LaunchAgent (auto-start on login)

PLIST_NAME="com.dictflow.app"
PLIST_PATH="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"
DICTFLOW_DIR="$HOME/dictflow"

cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    <key>ProgramArguments</key>
    <array>
        <string>${DICTFLOW_DIR}/venv/bin/python3</string>
        <string>${DICTFLOW_DIR}/main.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>${DICTFLOW_DIR}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/dictflow.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/dictflow.err</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
EOF

echo "LaunchAgent instalado en: $PLIST_PATH"
echo "DictFlow se iniciará automáticamente al iniciar sesión."
echo ""
echo "Para activar ahora:  launchctl load $PLIST_PATH"
echo "Para desactivar:     launchctl unload $PLIST_PATH"
echo "Para desinstalar:    rm $PLIST_PATH"
