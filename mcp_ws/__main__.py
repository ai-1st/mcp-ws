import argparse
import asyncio
import sys
import websockets
import os
import json
from datetime import datetime

async def connect_stdio_to_ws(url, headers=None, log_messages=None):
    try:
        headers_dict = {}
        if headers:
            try:
                headers_dict = json.loads(headers)
            except json.JSONDecodeError as e:
                print(f"Error parsing headers JSON: {e}", file=sys.stderr)
                sys.exit(1)
        
        # In websockets 15.0+, we need to use 'additional_headers' instead of 'extra_headers'
        async with websockets.connect(url, additional_headers=headers_dict) as ws:
            # Task to read from stdin and send to WebSocket
            async def send_stdin():
                # Keep stdin in blocking mode, but use asyncio to handle it properly
                loop = asyncio.get_event_loop()
                
                while True:
                    try:
                        # Use asyncio to read from stdin asynchronously in a way that won't block the event loop
                        line = await loop.run_in_executor(None, lambda: sys.stdin.readline())
                        
                        line = line.strip()
                        
                        if not line and not sys.stdin.isatty():  # EOF
                            break
                        
                        if line:  # Only send non-empty lines
                            if log_messages:
                                with open(log_messages, 'a') as f:
                                    f.write(f'> {line}\n')
                            await ws.send(line)
                    except BlockingIOError:
                        # If we get a blocking error, just wait a bit and try again
                        await asyncio.sleep(0.1)
                        continue
                    except Exception as e:
                        print(f"Error sending to WebSocket: {e}", file=sys.stderr)
                        break
                    
                    # Small sleep to prevent CPU hogging
                    await asyncio.sleep(0.1)

            # Task to receive from WebSocket and print to stdout
            async def receive_ws():
                try:
                    async for message in ws:
                        if log_messages:
                            with open(log_messages, 'a') as f:
                                f.write(f'< {message}\n')
                        print(message, flush=True)
                except Exception as e:
                    print(f"Error receiving from WebSocket: {e}", file=sys.stderr)

            # Run both tasks concurrently
            await asyncio.gather(send_stdin(), receive_ws())
    except Exception as e:
        print(f"WebSocket connection error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Connect local stdio to a remote WebSocket server"
    )
    parser.add_argument("url", help="WebSocket server URL (e.g., ws://example.com)")
    parser.add_argument(
        "--headers", 
        "-H", 
        help='Additional HTTP headers as JSON string (e.g., \'{"Authorization": "Bearer token"}\')'
    )
    parser.add_argument(
        "--log-messages",
        "-d",
        help="Write messages into a logfile for debugging purposes."
    )
    args = parser.parse_args()

    if args.log_messages:
        with open(args.log_messages, 'a') as f:
            f.write(f'Server started at {datetime.now()}\n')

    # Run the async WebSocket connection
    asyncio.run(connect_stdio_to_ws(args.url, args.headers, args.log_messages))


if __name__ == "__main__":
    main()