import asyncio
import logging
from jill_box.websocket_server import WebSocketServer

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s [%(name)s]: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

async def main():
    """Main entry point for the WebSocket server."""
    setup_logging()
    
    server = WebSocketServer(host="0.0.0.0", port=6969)
    
    try:
        await server.start()
    except KeyboardInterrupt:
        logging.info("Received shutdown signal")
    except Exception as e:
        logging.exception(f"Server error: {e}")
    finally:
        await server.shutdown()

if __name__ == "__main__":
    asyncio.run(main())