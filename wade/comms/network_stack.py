# -*- coding: utf-8 -*-
"""
WADE Network Stack
Provides network communication capabilities.
"""

import socket
import threading
import time
import json
import ssl
import queue
from typing import Dict, List, Any, Optional, Tuple, Callable


class NetworkStack:
    """
    Network Stack for WADE.
    Provides network communication capabilities.
    """

    def __init__(self):
        """Initialize the network stack."""
        self.servers = {}  # port -> server_info
        self.connections = {}  # connection_id -> connection_info
        self.connection_lock = threading.Lock()
        self.message_handlers = {}  # connection_id -> handler
        self.message_queues = {}  # connection_id -> queue
        self.is_running = True

    def start_server(
        self,
        port: int,
        handler: Callable,
        use_ssl: bool = False,
        ssl_cert: Optional[str] = None,
        ssl_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Start a server on the specified port.

        Args:
            port: Port to listen on
            handler: Function to handle incoming connections
            use_ssl: Whether to use SSL
            ssl_cert: Path to SSL certificate file
            ssl_key: Path to SSL key file

        Returns:
            Dictionary with server information
        """
        if port in self.servers:
            return {
                "status": "error",
                "message": f"Server already running on port {port}",
            }

        try:
            # Create server socket
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(("0.0.0.0", port))
            server_socket.listen(5)

            # Create SSL context if requested
            ssl_context = None
            if use_ssl:
                if not ssl_cert or not ssl_key:
                    return {
                        "status": "error",
                        "message": "SSL certificate and key required for SSL server",
                    }

                ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                ssl_context.load_cert_chain(certfile=ssl_cert, keyfile=ssl_key)

            # Create server info
            server_info = {
                "port": port,
                "socket": server_socket,
                "thread": None,
                "use_ssl": use_ssl,
                "ssl_context": ssl_context,
                "handler": handler,
                "status": "starting",
                "start_time": time.time(),
            }

            # Start server thread
            server_thread = threading.Thread(
                target=self._server_loop, args=(server_info,)
            )
            server_thread.daemon = True
            server_thread.start()

            server_info["thread"] = server_thread
            server_info["status"] = "running"

            # Store server info
            self.servers[port] = server_info

            return {"status": "success", "port": port, "use_ssl": use_ssl}

        except Exception as e:
            return {"status": "error", "message": f"Error starting server: {str(e)}"}

    def _server_loop(self, server_info: Dict[str, Any]):
        """
        Main server loop.

        Args:
            server_info: Server information
        """
        server_socket = server_info["socket"]
        port = server_info["port"]

        while self.is_running and server_info["status"] == "running":
            try:
                # Accept incoming connection
                client_socket, client_address = server_socket.accept()

                # Wrap socket in SSL if requested
                if server_info["use_ssl"] and server_info["ssl_context"]:
                    client_socket = server_info["ssl_context"].wrap_socket(
                        client_socket, server_side=True
                    )

                # Generate connection ID
                connection_id = (
                    f"{client_address[0]}:{client_address[1]}_{int(time.time() * 1000)}"
                )

                # Create connection info
                connection_info = {
                    "id": connection_id,
                    "socket": client_socket,
                    "address": client_address,
                    "server_port": port,
                    "thread": None,
                    "status": "connected",
                    "connect_time": time.time(),
                    "last_activity": time.time(),
                    "bytes_sent": 0,
                    "bytes_received": 0,
                }

                # Create message queue
                self.message_queues[connection_id] = queue.Queue()

                # Start connection thread
                connection_thread = threading.Thread(
                    target=self._connection_loop, args=(connection_info,)
                )
                connection_thread.daemon = True
                connection_thread.start()

                connection_info["thread"] = connection_thread

                # Store connection info
                with self.connection_lock:
                    self.connections[connection_id] = connection_info

                # Call connection handler
                try:
                    server_info["handler"](connection_id, client_address)
                except Exception as e:
                    print(f"Error in connection handler: {e}")

            except Exception as e:
                print(f"Error accepting connection: {e}")
                time.sleep(1)

    def _connection_loop(self, connection_info: Dict[str, Any]):
        """
        Main connection loop.

        Args:
            connection_info: Connection information
        """
        connection_id = connection_info["id"]
        client_socket = connection_info["socket"]

        while self.is_running and connection_info["status"] == "connected":
            try:
                # Check for outgoing messages
                if (
                    connection_id in self.message_queues
                    and not self.message_queues[connection_id].empty()
                ):
                    message = self.message_queues[connection_id].get()
                    self._send_message(connection_info, message)

                # Check for incoming data
                client_socket.settimeout(0.1)
                data = client_socket.recv(4096)

                if not data:
                    # Connection closed
                    self._close_connection(connection_id)
                    break

                # Update connection info
                connection_info["last_activity"] = time.time()
                connection_info["bytes_received"] += len(data)

                # Process received data
                self._process_received_data(connection_info, data)

            except socket.timeout:
                # No data available
                pass
            except Exception as e:
                print(f"Error in connection loop: {e}")
                self._close_connection(connection_id)
                break

    def _send_message(
        self, connection_info: Dict[str, Any], message: Dict[str, Any]
    ) -> bool:
        """
        Send a message to a connection.

        Args:
            connection_info: Connection information
            message: Message to send

        Returns:
            True if message was sent, False otherwise
        """
        try:
            # Convert message to JSON
            message_json = json.dumps(message)

            # Add message length prefix
            message_bytes = f"{len(message_json):10d}{message_json}".encode()

            # Send message
            connection_info["socket"].sendall(message_bytes)

            # Update connection info
            connection_info["last_activity"] = time.time()
            connection_info["bytes_sent"] += len(message_bytes)

            return True

        except Exception as e:
            print(f"Error sending message: {e}")
            return False

    def _process_received_data(self, connection_info: Dict[str, Any], data: bytes):
        """
        Process received data.

        Args:
            connection_info: Connection information
            data: Received data
        """
        connection_id = connection_info["id"]

        try:
            # Parse message
            message_length = int(data[:10].decode().strip())
            message_json = data[10 : 10 + message_length].decode()
            message = json.loads(message_json)

            # Call message handler if registered
            if (
                connection_id in self.message_handlers
                and self.message_handlers[connection_id]
            ):
                try:
                    self.message_handlers[connection_id](connection_id, message)
                except Exception as e:
                    print(f"Error in message handler: {e}")

        except Exception as e:
            print(f"Error processing received data: {e}")

    def send_message(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """
        Send a message to a connection.

        Args:
            connection_id: ID of the connection
            message: Message to send

        Returns:
            True if message was queued, False otherwise
        """
        if (
            connection_id not in self.connections
            or connection_id not in self.message_queues
        ):
            return False

        # Add message to queue
        self.message_queues[connection_id].put(message)

        return True

    def register_message_handler(self, connection_id: str, handler: Callable):
        """
        Register a message handler for a connection.

        Args:
            connection_id: ID of the connection
            handler: Function to handle incoming messages
        """
        self.message_handlers[connection_id] = handler

    def connect(
        self,
        host: str,
        port: int,
        use_ssl: bool = False,
        ssl_verify: bool = True,
        ssl_cert: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Connect to a remote server.

        Args:
            host: Host to connect to
            port: Port to connect to
            use_ssl: Whether to use SSL
            ssl_verify: Whether to verify SSL certificate
            ssl_cert: Path to SSL certificate file

        Returns:
            Dictionary with connection information
        """
        try:
            # Create socket
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            # Wrap socket in SSL if requested
            if use_ssl:
                ssl_context = ssl.create_default_context()

                if not ssl_verify:
                    ssl_context.check_hostname = False
                    ssl_context.verify_mode = ssl.CERT_NONE

                if ssl_cert:
                    ssl_context.load_verify_locations(ssl_cert)

                client_socket = ssl_context.wrap_socket(
                    client_socket, server_hostname=host
                )

            # Connect to server
            client_socket.connect((host, port))

            # Generate connection ID
            connection_id = f"client_{host}:{port}_{int(time.time() * 1000)}"

            # Create connection info
            connection_info = {
                "id": connection_id,
                "socket": client_socket,
                "address": (host, port),
                "server_port": None,
                "thread": None,
                "status": "connected",
                "connect_time": time.time(),
                "last_activity": time.time(),
                "bytes_sent": 0,
                "bytes_received": 0,
            }

            # Create message queue
            self.message_queues[connection_id] = queue.Queue()

            # Start connection thread
            connection_thread = threading.Thread(
                target=self._connection_loop, args=(connection_info,)
            )
            connection_thread.daemon = True
            connection_thread.start()

            connection_info["thread"] = connection_thread

            # Store connection info
            with self.connection_lock:
                self.connections[connection_id] = connection_info

            return {"status": "success", "connection_id": connection_id}

        except Exception as e:
            return {
                "status": "error",
                "message": f"Error connecting to server: {str(e)}",
            }

    def _close_connection(self, connection_id: str):
        """
        Close a connection.

        Args:
            connection_id: ID of the connection
        """
        with self.connection_lock:
            if connection_id in self.connections:
                connection_info = self.connections[connection_id]

                try:
                    connection_info["socket"].close()
                except:
                    pass

                connection_info["status"] = "disconnected"

                # Remove from connections
                del self.connections[connection_id]

            if connection_id in self.message_queues:
                del self.message_queues[connection_id]

            if connection_id in self.message_handlers:
                del self.message_handlers[connection_id]

    def close_connection(self, connection_id: str) -> bool:
        """
        Close a connection.

        Args:
            connection_id: ID of the connection

        Returns:
            True if connection was closed, False otherwise
        """
        if connection_id not in self.connections:
            return False

        self._close_connection(connection_id)
        return True

    def stop_server(self, port: int) -> bool:
        """
        Stop a server.

        Args:
            port: Port of the server

        Returns:
            True if server was stopped, False otherwise
        """
        if port not in self.servers:
            return False

        server_info = self.servers[port]

        try:
            # Close server socket
            server_info["socket"].close()

            # Update server info
            server_info["status"] = "stopped"

            # Remove from servers
            del self.servers[port]

            return True

        except Exception as e:
            print(f"Error stopping server: {e}")
            return False

    def get_connections(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all active connections.

        Returns:
            Dictionary of connection_id -> connection_info
        """
        with self.connection_lock:
            # Create a copy of connections with only public information
            connections = {}

            for connection_id, connection_info in self.connections.items():
                connections[connection_id] = {
                    "id": connection_info["id"],
                    "address": connection_info["address"],
                    "server_port": connection_info["server_port"],
                    "status": connection_info["status"],
                    "connect_time": connection_info["connect_time"],
                    "last_activity": connection_info["last_activity"],
                    "bytes_sent": connection_info["bytes_sent"],
                    "bytes_received": connection_info["bytes_received"],
                }

            return connections

    def get_servers(self) -> Dict[int, Dict[str, Any]]:
        """
        Get all active servers.

        Returns:
            Dictionary of port -> server_info
        """
        # Create a copy of servers with only public information
        servers = {}

        for port, server_info in self.servers.items():
            servers[port] = {
                "port": server_info["port"],
                "status": server_info["status"],
                "use_ssl": server_info["use_ssl"],
                "start_time": server_info["start_time"],
            }

        return servers

    def shutdown(self):
        """Shutdown the network stack."""
        self.is_running = False

        # Close all connections
        with self.connection_lock:
            for connection_id in list(self.connections.keys()):
                self._close_connection(connection_id)

        # Stop all servers
        for port in list(self.servers.keys()):
            self.stop_server(port)
