#!/usr/bin/env python3
import argparse
from terminal_component import start_api_server

def main():
    p = argparse.ArgumentParser(description='Start terminal API')
    p.add_argument('--port', '-p', type=int, default=8765)
    args = p.parse_args()
    port = args.port
    start_api_server(port)

if __name__ == '__main__':
    main()
