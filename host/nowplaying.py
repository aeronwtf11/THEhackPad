#!/usr/bin/env python3
# sends the current song to the hackpad, needs playerctl

import glob
import subprocess
import sys
import time
import unicodedata

FORMAT = "{{status}}\t{{title}}\t{{artist}}"


def find_port():
    ports = sorted(glob.glob("/dev/serial/by-id/*CircuitPython*-if02"))
    return ports[0] if ports else None


def ascii_only(text):
    text = unicodedata.normalize("NFKD", text)
    return text.encode("ascii", "ignore").decode().replace("\t", " ")


def line_for(raw):
    parts = raw.rstrip("\n").split("\t")
    if len(parts) < 3 or parts[0] != "Playing":
        return "\n"
    return ascii_only(parts[1]) + "\t" + ascii_only(parts[2]) + "\n"


def open_port(port):
    subprocess.run(["stty", "-F", port, "raw", "-echo"], check=False)
    return open(port, "w")


def main():
    fixed = sys.argv[1] if len(sys.argv) > 1 else None
    player = subprocess.Popen(
        ["playerctl", "metadata", "--follow", "--format", FORMAT],
        stdout=subprocess.PIPE, text=True,
    )
    out = None
    last = "\n"
    for raw in player.stdout:
        last = line_for(raw)
        while True:
            try:
                if out is None:
                    port = fixed or find_port()
                    if port is None:
                        raise OSError("hackpad not found")
                    out = open_port(port)
                out.write(last)
                out.flush()
                break
            except OSError as e:
                print(e, "- trying again in 3s")
                out = None
                time.sleep(3)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
