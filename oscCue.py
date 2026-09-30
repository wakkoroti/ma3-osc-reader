import socket
import re
import threading
import time
import json

from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn


# ============================================================
# CONFIGURATION
# ============================================================

# UDP port to listen on
LISTEN_PORT = 8000

# Web interface port
WEB_PORT = 8080

# Sequence names to look for
SEQUENCE_NAMES = [
    "TheShow",
    "Another One",
]


# ============================================================
# CURRENT STATE
# ============================================================

current_sequence = ""
current_cue = ""
current_cue_name = ""

# Protects the current state when accessed by
# the UDP listener and web server threads.
state_lock = threading.Lock()


# ============================================================
# UDP LISTENER
# ============================================================

def udp_listener():

    global current_sequence
    global current_cue
    global current_cue_name

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )

    # Allow the UDP port to be reused quickly
    # after restarting the program.
    sock.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )

    sock.bind(
        ("0.0.0.0", LISTEN_PORT)
    )

    # Prevent recvfrom() from blocking forever.
    # This allows Ctrl+C to work reliably.
    sock.settimeout(1.0)

    print(
        f"UDP listener started on port {LISTEN_PORT}"
    )

    try:

        while True:

            try:
                data, address = sock.recvfrom(65535)

            except socket.timeout:
                continue


            # ------------------------------------------------
            # Check each configured sequence name
            # ------------------------------------------------

            for sequence_name in SEQUENCE_NAMES:

                sequence_bytes = sequence_name.encode(
                    "utf-8"
                )


                # Find the sequence name in the
                # raw OSC packet.

                position = data.find(
                    sequence_bytes
                )


                if position == -1:
                    continue


                # There must be a byte immediately
                # before the sequence name.

                if position == 0:
                    continue


                # The byte immediately before the
                # sequence name MUST be 0x01.
                #
                # \x01TheShow 2 Cue  -> ACCEPT
                # \x00TheShow 2 Cue  -> IGNORE

                if data[position - 1] != 0x01:
                    continue


                # ------------------------------------------------
                # Decode from the sequence name onward
                # ------------------------------------------------

                message = data[position:].decode(
                    "utf-8",
                    errors="ignore"
                )


                # Look for:
                #
                # Sequence Name <number> Cue
                #
                # Examples:
                #
                # TheShow 2 Cue
                # Another One 140.1 Cue
                #
                # Cue numbers can be integers or decimals.

                pattern = (
                    re.escape(sequence_name)
                    + r"\s+([0-9]{1,4}(?:\.[0-9]{1,4})?)\s+([^\x00]+)"
                )


                match = re.search(
                    pattern,
                    message,
                    re.IGNORECASE
                )


                if match:

                    cue_number = match.group(1)
                    cue_name = match.group(2)


                    # Update the information displayed
                    # by the web interface.

                    with state_lock:

                        current_sequence = sequence_name
                        current_cue = cue_number
                        current_cue_name = cue_name


                    # Console output is useful while testing.

                    print(
                        f"Seq: {current_sequence} "
                        f"Cue: {current_cue} "
                        f"Name: {current_cue_name}"
                    )


                    # We found a valid sequence.

                    break


    except Exception as e:

        print(
            f"UDP listener error: {e}"
        )


    finally:

        sock.close()

        print(
            "UDP socket closed."
        )


# ============================================================
# WEB PAGE
# ============================================================

HTML_PAGE = """
<!DOCTYPE html>
<html>

<head>

    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>OSC MA3 Cue Monitor</title>

    <style>

        body {
            margin: 0;
            background: #111;
            color: white;
            font-family:
                Arial,
                Helvetica,
                sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .container { 
            border-radius: 5px;
  	        border: 1px solid white;
            font: normal 20px/1 "Inspire", "helvetica neue", helvetica, arial, sans-serif;
            text-align: center;
            text-shadow: 1px 1px rgba(0, 0, 0, 0);
            margin: 0px auto 0;
            padding: 5px;
            font-size: 100%;
			background-repeat:no-repeat;
            width: 650px;
            height: 150px;
            vertical-align: middle;
		}
        .label {
            font-size: 28px;
            color: #888;
            text-align: right;
            vertical-align: middle;
        }
        .sequence {
            font-size: 28px;
            color: #888;
            vertical-align: middle;
        }
        .cue {
            font-size: 100px;
            font-weight: bold;
            vertical-align: middle;
        }

    </style>

</head>


<body>

    <table class="container">
        <colgroup>
            <col style="width:50%">
            <col style="width:40%">
        </colgroup>
        <tr>
            <td class="label">LIGHTING SEQUENCE&nbsp&nbsp&nbsp</td>
            <td class="sequence" id="sequence"></td>
        </tr>
        <tr style="height:110px;">
            <td class="label">CUE&nbsp&nbsp&nbsp </td>
            <td class="cue" id="cue"></td>
        </tr>
        <tr>
            <td class="label">CUE NAME&nbsp&nbsp&nbsp</td>
            <td class="sequence" id="cuename"></td>
        </tr>
        
    </table>


    <script>

        // Connect to the Python server
        // using Server-Sent Events.

        const events =
            new EventSource("/events");


        events.onmessage = function(event) {

            const data =
                JSON.parse(event.data);


            document.getElementById(
                "sequence"
            ).textContent = data.sequence;


            document.getElementById(
                "cue"
            ).textContent = data.cue;

            
            document.getElementById(
                "cuename"
            ).textContent = data.cuename;

        };


        // The browser will automatically attempt
        // to reconnect if the Python server
        // temporarily disappears.

        events.onerror = function() {

            // Nothing needed here.
            // EventSource automatically reconnects.

        };

    </script>

</body>

</html>
"""


# ============================================================
# THREADED WEB SERVER
# ============================================================

class ThreadedHTTPServer(
    ThreadingMixIn,
    HTTPServer
):

    # Allows the server to reuse the port
    # immediately after restarting.

    allow_reuse_address = True

    # Don't wait for browser connections to
    # finish before shutting down.

    daemon_threads = True


# ============================================================
# WEB SERVER
# ============================================================

class WebHandler(
    BaseHTTPRequestHandler
):

    # ========================================================
    # CATCH BROWSER DISCONNECTS AT THE HTTP LEVEL
    # ========================================================

    def handle(self):

        try:

            super().handle()

        except (
            BrokenPipeError,
            ConnectionAbortedError,
            ConnectionResetError
        ):

            # Browser disconnected.
            #
            # This is normal when:
            # - Page is refreshed
            # - Browser tab is closed
            # - Browser navigates somewhere else
            # - Python is stopped
            # - Python is restarted
            #
            # Do not print an error.

            pass


    # ========================================================
    # WEB REQUEST
    # ========================================================

    def do_GET(self):

        try:

            # ====================================================
            # Main web page
            # ====================================================

            if self.path == "/":

                self.send_response(200)

                self.send_header(
                    "Content-Type",
                    "text/html; charset=utf-8"
                )

                self.send_header(
                    "Cache-Control",
                    "no-cache"
                )

                self.end_headers()

                self.wfile.write(
                    HTML_PAGE.encode("utf-8")
                )

                self.wfile.flush()

                return


            # ====================================================
            # Server-Sent Events
            # ====================================================

            elif self.path == "/events":

                self.send_response(200)

                self.send_header(
                    "Content-Type",
                    "text/event-stream"
                )

                self.send_header(
                    "Cache-Control",
                    "no-cache"
                )

                self.send_header(
                    "Connection",
                    "keep-alive"
                )

                self.end_headers()


                # Get current state

                with state_lock:

                    sequence = current_sequence
                    cue = current_cue
                    cuename = current_cue_name


                # Send current state immediately

                self.send_current_state(
                    sequence,
                    cue,
                    cuename
                )


                # Remember what was sent

                last_sequence = sequence
                last_cue = cue
                last_cuename = cuename


                # Wait for changes

                while True:

                    time.sleep(0.1)

                    with state_lock:

                        sequence = current_sequence
                        cue = current_cue
                        cuename = current_cue_name


                    # Only send when something changes

                    if (
                        sequence != last_sequence
                        or cue != last_cue
                        or cuename != last_cuename
                    ):

                        self.send_current_state(
                            sequence,
                            cue,
                            cuename
                        )

                        last_sequence = sequence
                        last_cue = cue
                        last_cuename = cuename

                return


            # ====================================================
            # Unknown URL
            # ====================================================

            else:

                self.send_response(404)
                self.end_headers()

                return


        except (
            BrokenPipeError,
            ConnectionAbortedError,
            ConnectionResetError
        ):

            # Browser disconnected while processing
            # the request.

            return


    # ========================================================
    # SEND CURRENT STATE
    # ========================================================

    def send_current_state(
        self,
        sequence,
        cue,
        cuename
    ):

        data = json.dumps({
            "sequence": sequence,
            "cue": cue,
            "cuename": cuename
        })

        message = (
            f"data: {data}\n\n"
        )

        self.wfile.write(
            message.encode("utf-8")
        )

        self.wfile.flush()


    # ========================================================
    # KEEP CONSOLE QUIET
    # ========================================================

    def log_message(
        self,
        format,
        *args
    ):

        pass

# ============================================================
# START WEB SERVER
# ============================================================

def start_web_server():

    server = ThreadedHTTPServer(
        ("0.0.0.0", WEB_PORT),
        WebHandler
    )


    print(
        "Web interface available at:"
    )

    print(
        f"  http://localhost:{WEB_PORT}"
    )


    try:

        server.serve_forever(
            poll_interval=0.5
        )


    finally:

        print(
            "Stopping web server..."
        )

        server.shutdown()

        server.server_close()

        print(
            "Web server stopped."
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "=" * 60
    )

    print(
        "OSC Sequence Monitor"
    )

    print(
        "=" * 60
    )


    print(
        f"UDP Port : {LISTEN_PORT}"
    )

    print(
        f"Web Port : {WEB_PORT}"
    )


    print(
        "\nSequences being monitored:"
    )


    for name in SEQUENCE_NAMES:

        print(
            f"  {name}"
        )


    print(
        "\nPress Ctrl+C to stop."
    )


    print(
        "=" * 60
    )

    print()


    # --------------------------------------------------------
    # Start UDP listener in background
    # --------------------------------------------------------

    udp_thread = threading.Thread(
        target=udp_listener,
        daemon=True
    )

    udp_thread.start()


    # --------------------------------------------------------
    # Run web server
    # --------------------------------------------------------

    try:

        start_web_server()


    except KeyboardInterrupt:

        print(
            "\nStopping..."
        )


    print(
        "Program stopped."
    )