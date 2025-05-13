import argparse
import asyncio
import sys
import websockets
import os
import json


async def connect_stdio_to_ws(url, headers=None):
    try:
        extra_headers = {}
        if headers:
            try:
                extra_headers = json.loads(headers)
            except json.JSONDecodeError as e:
                print(f"Error parsing headers JSON: {e}", file=sys.stderr)
                sys.exit(1)
        
        async with websockets.connect(url, extra_headers=extra_headers) as ws:
            # Task to read from stdin and send to WebSocket
            async def send_stdin():
                # Set stdin to non-blocking mode
                if os.name != 'nt':  # Not Windows
                    import fcntl
                    fd = sys.stdin.fileno()
                    fl = fcntl.fcntl(fd, fcntl.F_GETFL)
                    fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
                
                loop = asyncio.get_event_loop()
                
                while True:
                    try:
                        # Use asyncio to read from stdin asynchronously
                        line = await loop.run_in_executor(None, sys.stdin.readline)
                        line = line.strip()
                        
                        if not line and not sys.stdin.isatty():  # EOF
                            break
                            
                        if line:  # Only send non-empty lines
                            await ws.send(line)
                    except Exception as e:
                        print(f"Error sending to WebSocket: {e}", file=sys.stderr)
                        break
                    
                    # Small sleep to prevent CPU hogging
                    await asyncio.sleep(0.01)

            # Task to receive from WebSocket and print to stdout
            async def receive_ws():
                try:
                    async for message in ws:
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
    args = parser.parse_args()

    # Run the async WebSocket connection
    asyncio.run(connect_stdio_to_ws(args.url, args.headers))


if __name__ == "__main__":
    main()