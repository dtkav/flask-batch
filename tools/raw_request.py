#!/usr/bin/env python

import socket
import argparse


def main(filename, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(("localhost", port))

    with open(filename, "rb") as f:
        s.send(f.read())
        s.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    parser.add_argument("--port", default=5000, type=int)
    args = parser.parse_args()
    main(args.filename, args.port)
