import argparse
import sys
import threading
import json
import logging
from websockets.sync.client import connect
from websockets.exceptions import ConnectionClosed, WebSocketException


def setup_logging(logfile):
    """Configure logging to a file if specified."""
    if logfile:
        logging.basicConfig(
            filename=logfile,
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
        )


def main():
    parser = argparse.ArgumentParser(
        description="Connect local stdio to a remote WebSocket server"
    )
    parser.add_argument("url", help="WebSocket server URL (e.g., ws://example.com)")
    parser.add_argument(
        "--headers",
        "-H",
        help='Additional HTTP headers as JSON string (e.g., \'{"Authorization": "Bearer token"}\')',
    )
    parser.add_argument(
        "--log-messages",
        "-L",
        help="Write messages into a logfile for debugging purposes.",
    )
    args = parser.parse_args()

    # Set up logging if specified
    setup_logging(args.log_messages)

    # Parse headers if provided
    headers = {}
    if args.headers:
        try:
            headers = json.loads(args.headers)
            if not isinstance(headers, dict):
                logging.error("Headers must be a JSON object")
                sys.exit(1)
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing headers JSON: {e}")
            sys.exit(1)

    # Flag to signal shutdown
    shutdown_event = threading.Event()

    def send_stdin(websocket):
        """Synchronously read from stdin and send to WebSocket."""
        try:
            while not shutdown_event.is_set():
                line = sys.stdin.readline().strip()
                if not line:  # EOF or empty input
                    break
                try:
                    websocket.send(line)
                    if args.log_messages:
                        logging.debug(f"Sent: {line}")
                except WebSocketException as e:
                    logging.error(f"Error sending message: {e}")
                    shutdown_event.set()
        except Exception as e:
            logging.error(f"Error reading stdin: {e}")
        finally:
            shutdown_event.set()

    try:
        with connect(args.url, additional_headers=headers) as websocket:
            # Start thread to read stdin and send synchronously
            stdin_thread = threading.Thread(target=send_stdin, args=(websocket,))
            stdin_thread.daemon = True
            stdin_thread.start()

            # Main thread receives messages and prints to stdout
            while not shutdown_event.is_set():
                try:
                    message = websocket.recv(timeout=1.0)
                    print(message, flush=True)
                    if args.log_messages:
                        logging.debug(f"Received: {message}")
                except TimeoutError:
                    continue
                except ConnectionClosed:
                    logging.error("WebSocket connection closed")
                    shutdown_event.set()
                    break
                except WebSocketException as e:
                    logging.error(f"Error receiving message: {e}")
                    shutdown_event.set()
                    break

    except WebSocketException as e:
        logging.error(f"WebSocket connection error: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        sys.exit(1)
    finally:
        shutdown_event.set()
        stdin_thread.join(timeout=1.0)


if __name__ == "__main__":
    main()