# Brightsign Remote Management Tool

A streamlined utility designed to interact with BrightSign digital signage players. It enables efficient reinstallation of autorun applications and fast screenshot capture, either for individual devices or across multiple players at once.

## Features

### Autorun Reinstallation

- **Single Player Mode**  
  Input the player's IP address, password, and optionally its serial number (used as a fallback password). Upload or select an existing autorun file. The tool will handle the entire reinstallation process.

- **Multi Player Mode**  
  Upload a CSV file with player information. The tool will automatically process all devices listed and perform the same reinstallation steps.

**Time-saving benefit:** Eliminates the need to wait for reboots and perform manual reinstallations across devices.

### Screenshot Capture

- **Single Player Mode**  
  Input the player's IP address, password, and optional serial number. Capture a current-frame screenshot or enable continuous mode to fetch screenshots every 5 to 60 seconds.

- **Multi Player Mode**  
  Upload a CSV file with player information and the tool will fetch and display screenshots from all listed players.

**Use case:** Enables real-time monitoring of multiple devices for diagnostics or status verification without manual logins.

### Autorun File Management

Save autorun files within the application for future use. This removes the need to upload the file each time you reinstall it on a player.

---

## Getting Started

### Requirements

- Python must be installed on the system

### Launch Instructions

1. Place all application files in a folder.
2. Open a terminal in that folder and run:

```
py run.py
```

This will:

- Automatically create a Python virtual environment
- Install all required dependencies
- Launch the app in your default browser using Streamlit

This command is used to run the application every time.

## Contributing

Contributions are welcome. If you'd like to report a bug or suggest a feature, feel free to open an issue or submit a pull request.