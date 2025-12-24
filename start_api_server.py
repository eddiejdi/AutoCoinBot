#!/usr/bin/env python3
import sys
import os
import time
here = os.path.abspath(os.path.dirname(__file__))
parent = os.path.dirname(here)
if parent not in sys.path:
    sys.path.insert(0, parent)

from terminal_component import start_api_server

if __name__ == "__main__":
    port = start_api_server(8765)
    if port:
        print(f"API server started on port {port}")
        # Keep the main thread alive to prevent daemon threads from dying
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down API server")
    else:
        print("Failed to start API server")