# grandMA3 OSC Sequence Monitor

A Python application that listens for OSC-related UDP messages from a grandMA3 lighting console and displays the active sequence, cue number, and cue name in a web browser.

## Features

- Listens for UDP messages from grandMA3.
- Monitors multiple lighting sequences.
- Displays the sequence name, cue number, and cue name in a browser.
- Updates the display automatically when the active cue changes.
- Supports integer and decimal cue numbers up to `9999.9999`.
- Configurable UDP and HTTP ports.
- Supports command-line overrides without editing the configuration file.
- Uses Python's standard library; no third-party packages are required.

## Requirements

- Python 3.10 or later recommended.
- grandMA3 console or onPC.
- A web browser on the computer running the application, or another computer on the same network.

## Configuration of Application

Edit `config.py` to set the default ports and sequence names.

```python
# UDP port receiving messages from grandMA3
LISTEN_PORT = 8000

# HTTP port serving the web interface
WEB_PORT = 8080

# Sequence names to monitor - these are case-sensitive
SEQUENCE_NAMES = [
    "TheShow",
    "Another One",
]
```

These settings are used whenever a corresponding command-line override is not supplied.

## Configuration of GrandMA3
- Start a network session on the MA3.
- Open settings menu and open *In & Out*.
- Switch to the *OSC* tab and enter in the IP address of the computer where the python app is running.
- The port should match what you have configured the UDP Port as in the python application.
- Scroll right in the configuration and change *Send* to `Yes`.
    - If you wish to log the outgoing command in the System Monitor, then change *Echo Output* to `Yes`
- Toggle the *Enable Output* button on.
- If you have followed the above (and have Echo Output set to Yes), you should see outgoing messages when you hit **GO** on an executor, in the MA3 System Monitor.

## Starting the Application

Open a terminal or Command Prompt in the project directory and run:

```bat
python oscCue.py
```

The application prints the active configuration and starts listening for UDP messages.

Open the web interface:

```text
http://localhost:8080
```

To view the interface from another computer on the network, use the IP address of the computer running the application, for example:

```text
http://192.168.1.100:8080
```

Replace the example address with the actual IP address of the host computer. Windows Firewall may need an inbound rule for the web port.

## Command-Line Options

| Option | Description |
|---|---|
| `--help` | Display help for all available arguments. |
| `--listen-port PORT` | Override the UDP listening port configured in `config.py`. |
| `--web-port PORT` | Override the web interface port configured in `config.py`. |
| `--sequence NAME` | Monitor a specified sequence instead of the configured sequence list. Can be repeated to specify multiple sequences. |

### Override the UDP Port

```bat
python oscCue.py --listen-port 8001
```

The application listens for UDP messages on port `8001`. The web port and sequence names remain configured as defined in `config.py`.

### Override the Web Port

```bat
python oscCue.py --web-port 8081
```

Open the interface at:

```text
http://localhost:8081
```

### Override Both Ports

```bat
python oscCue.py --listen-port 8001 --web-port 8081
```

### Monitor a Single Sequence

```bat
python oscCue.py --sequence "TheShow"
```

When `--sequence` is provided, the configured sequence list is replaced by the command-line sequence list.

### Monitor Multiple Sequences

Repeat `--sequence` for each sequence name:

```bat
python oscCue.py --sequence "TheShow" --sequence "Another One"
```

Sequence names containing spaces must be enclosed in quotes.

### Override Ports and Sequence Names Together

```bat
python oscCue.py --listen-port 8001 --web-port 8081 --sequence "DAY TWO" --sequence "Holiday Show"
```

This example listens on UDP port `8001`, serves the web interface on port `8081`, and monitors only `DAY TWO` and `Holiday Show`.

## Network and Troubleshooting

### Web Port Already in Use

If the web server cannot start because the port is unavailable, try another port:

```bat
python oscCue.py --web-port 8081
```

### No Cue Information Appears

Check that:

- The UDP port matches the port configured as the destination on the grandMA3 side.
- The host firewall allows the incoming UDP traffic.
- The sequence name in `config.py` or the command line matches the sequence name in the incoming message.
- The incoming packet contains the expected sequence information and the required `0x01` byte immediately before the sequence name.

### Stopping the Application

Press `Ctrl+C` in the terminal where the program is running.

## Notes

- The UDP listening port and web interface port serve different purposes.
- Changing the UDP port requires the grandMA3 message destination to use the same port.
- Changing the web port changes the URL used to open the browser interface.
- Command-line overrides apply only to the current run; they do not modify `config.py`.

