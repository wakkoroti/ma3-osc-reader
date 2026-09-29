import socket
import re

# ============================================================
# CONFIGURATION
# ============================================================

# UDP port to listen on
LISTEN_PORT = 8000

# Sequence names to look for
SEQUENCE_NAMES = [
    "TheShow",
    "Band Show",
]


# ============================================================
# UDP LISTENER
# ============================================================

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Listen on all network interfaces
sock.bind(("0.0.0.0", LISTEN_PORT))

# Prevent recvfrom() from blocking forever.
# This allows Ctrl+C to reliably stop the script on Windows.
sock.settimeout(1.0)


print("=" * 60)
print("OSC UDP Sequence Listener")
print("=" * 60)
print(f"Listening on UDP port: {LISTEN_PORT}")
print("Looking for sequences:")

for name in SEQUENCE_NAMES:
    print(f"  - {name}")

print("\nPress Ctrl+C to stop.")
print("=" * 60)
print()


try:
    while True:

        # --------------------------------------------------------
        # Wait for an OSC packet
        # --------------------------------------------------------

        try:
            data, address = sock.recvfrom(65535)

        except socket.timeout:
            continue

        # --------------------------------------------------------
        # Check every configured sequence name
        # --------------------------------------------------------

        for sequence_name in SEQUENCE_NAMES:

            # Convert the sequence name to bytes.
            sequence_bytes = sequence_name.encode("utf-8")

            # We specifically want:
            #
            #     \x01TheShow 2 Cue
            #
            # and NOT:
            #
            #     \x00TheShow 2 Cue
            #
            #
            # Find the sequence name in the original UDP bytes.
            position = data.find(sequence_bytes)

            if position == -1:
                continue

            # Make sure there is a byte immediately before
            # the sequence name.
            if position == 0:
                continue

            # Check that the preceding byte is exactly 0x01.
            if data[position - 1] != 0x01:
                continue

            # ----------------------------------------------------
            # Sequence name found with the required 0x01 prefix.
            # Now look for the cue number.
            # ----------------------------------------------------

            # Decode the portion starting with the sequence name.
            message = data[position:].decode(
                "utf-8",
                errors="ignore"
            )

            # Look for:
            #
            #     Sequence Name <number> Cue
            #
            # Examples:
            #
            #     TheShow 2 Cue
            #     Another One 140.1 Cue
            #
            # Cue numbers can be integers or decimals.

            pattern = (
                re.escape(sequence_name)
                + r"\s+([0-9]+(?:\.[0-9]+)?)\s+Cue\b"
            )

            match = re.search(
                pattern,
                message,
                re.IGNORECASE
            )

            if match:

                cue_number = match.group(1)

                print(
                    f"Seq: {sequence_name} "
                    f"Cue: {cue_number}"
                )

                # We found a valid match.
                break


except KeyboardInterrupt:
    print("\n")
    print("Listener stopped.")


finally:
    sock.close()
    print("Socket closed.")