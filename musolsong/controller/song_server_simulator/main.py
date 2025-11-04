"""MUSOLGSONG SONG server simulator software system"""

import sys
import logging
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler

from musolsong.controller.song_server_simulator.xmlrpc_song_server_simulator import SONGSpectrographSimulator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('song_server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)
class RequestHandler(SimpleXMLRPCRequestHandler):
    """Custom request handler for logging."""
    
    def log_request(self, code='-', size='-'):
        """Log incoming requests."""
        logger.info(f"XML-RPC request from {self.client_address[0]}:{self.client_address[1]} - {code}")


def main():
    """Main server function."""
    
    # Server configuration
    HOST = "127.0.0.1"  # Listen on all interfaces 127.0.0.1
    PORT = 8050
    
    print("=" * 70)
    print("SONG Spectrograph Server Simulator")
    print("=" * 70)
    print(f"Starting server on {HOST}:{PORT}")
    print("Available methods:")
    print("  - acquire_a_solar_image(proj_nr, proj_name, exptime, imagetype,")
    print("                         alpha_deg, beta_deg, calibration_theta_deg, comment)")
    print("  - ping()")
    print("  - get_status()")
    print("  - get_capabilities()")
    print("=" * 70)
    
    # Create the server
    try:
        server = SimpleXMLRPCServer(
            (HOST, PORT),
            requestHandler=RequestHandler,
            allow_none=True
        )
        
        # Create detector instance
        detector = SONGSpectrographSimulator()
        
        # Register methods
        server.register_instance(detector)
        server.register_introspection_functions()
        
        logger.info(f"Server started successfully on {HOST}:{PORT}")
        logger.info("Waiting for client connections...")
        
        # Start serving
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server shutdown requested")
            
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
    
    finally:
        logger.info("Server stopped")
        print("\nServer stopped")


if __name__ == "__main__":
    main()
