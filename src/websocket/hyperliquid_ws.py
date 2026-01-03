"""
Moon Dev's Hyperliquid WebSocket Client
Real-time data feed for trading agents
Built with love by Moon Dev

Features:
- Real-time order book, trades, and candle data
- Automatic reconnection with exponential backoff
- Graceful connection drop handling
- Comprehensive error logging
- Thread-safe message handling
"""

import json
import time
import threading
import logging
from typing import Callable, Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

try:
    import websocket
except ImportError:
    raise ImportError("websocket-client package required. Install with: pip install websocket-client")

from termcolor import cprint

# Configure module logger
logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    """WebSocket connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    CLOSED = "closed"


class SubscriptionType(Enum):
    """Available subscription types for Hyperliquid WebSocket"""
    L2_BOOK = "l2Book"
    TRADES = "trades"
    CANDLE = "candle"
    ALL_MIDS = "allMids"
    USER_EVENTS = "userEvents"
    USER_FILLS = "userFills"
    USER_FUNDINGS = "userFundings"
    USER_NON_FUNDING_LEDGER_UPDATES = "userNonFundingLedgerUpdates"
    WEB_DATA2 = "webData2"
    NOTIFICATION = "notification"
    ORDER_UPDATES = "orderUpdates"


class HyperliquidWebSocket:
    """
    Hyperliquid WebSocket client for real-time market data

    Usage:
        ws = HyperliquidWebSocket()
        ws.on_message = my_callback_function
        ws.connect()
        ws.subscribe_l2_book("BTC")
        ws.subscribe_trades("ETH")
        ...
        ws.close()
    """

    # WebSocket endpoint
    WS_URL = "wss://api.hyperliquid.xyz/ws"

    # Reconnection settings
    MAX_RECONNECT_ATTEMPTS = 10
    INITIAL_RECONNECT_DELAY = 1.0  # seconds
    MAX_RECONNECT_DELAY = 60.0  # seconds
    RECONNECT_BACKOFF_MULTIPLIER = 2.0

    # Heartbeat settings
    PING_INTERVAL = 30  # seconds
    PING_TIMEOUT = 10  # seconds

    def __init__(
        self,
        on_message: Optional[Callable[[Dict], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        on_connect: Optional[Callable[[], None]] = None,
        on_disconnect: Optional[Callable[[bool], None]] = None,
        auto_reconnect: bool = True,
        log_level: int = logging.INFO
    ):
        """
        Initialize the Hyperliquid WebSocket client

        Args:
            on_message: Callback for received messages
            on_error: Callback for errors
            on_connect: Callback when connected
            on_disconnect: Callback when disconnected (arg: was_clean)
            auto_reconnect: Enable automatic reconnection
            log_level: Logging level (default: INFO)
        """
        # Callbacks
        self._on_message_callback = on_message
        self._on_error_callback = on_error
        self._on_connect_callback = on_connect
        self._on_disconnect_callback = on_disconnect

        # Settings
        self._auto_reconnect = auto_reconnect
        self._should_reconnect = True

        # Connection state
        self._state = ConnectionState.DISCONNECTED
        self._ws: Optional[websocket.WebSocketApp] = None
        self._ws_thread: Optional[threading.Thread] = None
        self._reconnect_attempt = 0
        self._last_message_time: Optional[datetime] = None

        # Subscriptions tracking
        self._subscriptions: List[Dict] = []
        self._lock = threading.Lock()

        # Configure logging
        self._setup_logging(log_level)

        cprint("WebSocket client initialized", "cyan")

    def _setup_logging(self, log_level: int):
        """Configure logging for the WebSocket client"""
        logger.setLevel(log_level)
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(log_level)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

    @property
    def state(self) -> ConnectionState:
        """Get current connection state"""
        return self._state

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected"""
        return self._state == ConnectionState.CONNECTED

    @property
    def on_message(self) -> Optional[Callable]:
        """Get message callback"""
        return self._on_message_callback

    @on_message.setter
    def on_message(self, callback: Callable[[Dict], None]):
        """Set message callback"""
        self._on_message_callback = callback

    def connect(self) -> bool:
        """
        Connect to the Hyperliquid WebSocket

        Returns:
            bool: True if connection initiated successfully
        """
        if self._state in [ConnectionState.CONNECTED, ConnectionState.CONNECTING]:
            cprint("Already connected or connecting", "yellow")
            return False

        self._should_reconnect = True
        self._state = ConnectionState.CONNECTING
        self._reconnect_attempt = 0

        cprint(f"Connecting to {self.WS_URL}...", "cyan")
        logger.info(f"Initiating connection to {self.WS_URL}")

        return self._create_connection()

    def _create_connection(self) -> bool:
        """Create WebSocket connection"""
        try:
            self._ws = websocket.WebSocketApp(
                self.WS_URL,
                on_open=self._handle_open,
                on_message=self._handle_message,
                on_error=self._handle_error,
                on_close=self._handle_close,
                on_ping=self._handle_ping,
                on_pong=self._handle_pong
            )

            # Run WebSocket in a separate thread
            self._ws_thread = threading.Thread(
                target=self._run_websocket,
                daemon=True,
                name="HyperliquidWS"
            )
            self._ws_thread.start()

            return True

        except Exception as e:
            logger.error(f"Failed to create WebSocket connection: {e}")
            cprint(f"Connection failed: {e}", "red")
            self._state = ConnectionState.DISCONNECTED
            return False

    def _run_websocket(self):
        """Run the WebSocket event loop"""
        try:
            self._ws.run_forever(
                ping_interval=self.PING_INTERVAL,
                ping_timeout=self.PING_TIMEOUT,
                ping_payload="ping"
            )
        except Exception as e:
            logger.error(f"WebSocket run_forever error: {e}")

    def _handle_open(self, ws):
        """Handle WebSocket connection opened"""
        self._state = ConnectionState.CONNECTED
        self._reconnect_attempt = 0
        self._last_message_time = datetime.now()

        cprint("WebSocket connected!", "green")
        logger.info("WebSocket connection established")

        # Resubscribe to previous subscriptions
        self._resubscribe()

        # Call user callback
        if self._on_connect_callback:
            try:
                self._on_connect_callback()
            except Exception as e:
                logger.error(f"Error in on_connect callback: {e}")

    def _handle_message(self, ws, message: str):
        """Handle incoming WebSocket message"""
        self._last_message_time = datetime.now()

        try:
            data = json.loads(message)
            logger.debug(f"Received message: {data}")

            # Handle different message types
            if "channel" in data:
                channel = data.get("channel")
                msg_data = data.get("data", {})

                logger.debug(f"Channel: {channel}, Data keys: {msg_data.keys() if isinstance(msg_data, dict) else 'N/A'}")

            # Call user callback
            if self._on_message_callback:
                try:
                    self._on_message_callback(data)
                except Exception as e:
                    logger.error(f"Error in on_message callback: {e}")
                    cprint(f"Message callback error: {e}", "red")

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse message as JSON: {e}")
            logger.debug(f"Raw message: {message}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    def _handle_error(self, ws, error: Exception):
        """Handle WebSocket error"""
        error_msg = str(error)
        logger.error(f"WebSocket error: {error_msg}")
        cprint(f"WebSocket error: {error_msg}", "red")

        # Call user callback
        if self._on_error_callback:
            try:
                self._on_error_callback(error)
            except Exception as e:
                logger.error(f"Error in on_error callback: {e}")

    def _handle_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket connection closed"""
        was_clean = close_status_code == 1000

        logger.info(f"WebSocket closed: code={close_status_code}, msg={close_msg}")

        if was_clean:
            cprint("WebSocket connection closed cleanly", "yellow")
        else:
            cprint(f"WebSocket connection dropped: {close_msg}", "red")

        # Call user callback
        if self._on_disconnect_callback:
            try:
                self._on_disconnect_callback(was_clean)
            except Exception as e:
                logger.error(f"Error in on_disconnect callback: {e}")

        # Attempt reconnection if enabled and not intentionally closed
        if self._auto_reconnect and self._should_reconnect:
            self._attempt_reconnect()
        else:
            self._state = ConnectionState.CLOSED

    def _handle_ping(self, ws, message):
        """Handle ping from server"""
        logger.debug("Received ping from server")

    def _handle_pong(self, ws, message):
        """Handle pong response from server"""
        logger.debug("Received pong from server")

    def _attempt_reconnect(self):
        """Attempt to reconnect with exponential backoff"""
        if self._reconnect_attempt >= self.MAX_RECONNECT_ATTEMPTS:
            logger.error(f"Max reconnection attempts ({self.MAX_RECONNECT_ATTEMPTS}) reached")
            cprint("Max reconnection attempts reached. Giving up.", "red")
            self._state = ConnectionState.CLOSED
            return

        self._state = ConnectionState.RECONNECTING
        self._reconnect_attempt += 1

        # Calculate delay with exponential backoff
        delay = min(
            self.INITIAL_RECONNECT_DELAY * (self.RECONNECT_BACKOFF_MULTIPLIER ** (self._reconnect_attempt - 1)),
            self.MAX_RECONNECT_DELAY
        )

        logger.info(f"Reconnection attempt {self._reconnect_attempt}/{self.MAX_RECONNECT_ATTEMPTS} in {delay:.1f}s")
        cprint(f"Reconnecting in {delay:.1f}s (attempt {self._reconnect_attempt}/{self.MAX_RECONNECT_ATTEMPTS})...", "yellow")

        # Wait before reconnecting
        time.sleep(delay)

        # Attempt reconnection if still should reconnect
        if self._should_reconnect:
            self._create_connection()

    def _resubscribe(self):
        """Resubscribe to all previous subscriptions after reconnection"""
        with self._lock:
            if not self._subscriptions:
                return

            logger.info(f"Resubscribing to {len(self._subscriptions)} channels")
            cprint(f"Resubscribing to {len(self._subscriptions)} channels...", "cyan")

            for subscription in self._subscriptions:
                try:
                    self._send_subscription(subscription, subscribe=True)
                except Exception as e:
                    logger.error(f"Failed to resubscribe: {e}")

    def _send(self, message: Dict) -> bool:
        """Send a message through the WebSocket"""
        if not self.is_connected or not self._ws:
            logger.warning("Cannot send message: not connected")
            return False

        try:
            self._ws.send(json.dumps(message))
            logger.debug(f"Sent message: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False

    def _send_subscription(self, subscription: Dict, subscribe: bool = True) -> bool:
        """Send a subscription/unsubscription request"""
        message = {
            "method": "subscribe" if subscribe else "unsubscribe",
            "subscription": subscription
        }
        return self._send(message)

    def _add_subscription(self, subscription: Dict):
        """Track a subscription"""
        with self._lock:
            if subscription not in self._subscriptions:
                self._subscriptions.append(subscription)

    def _remove_subscription(self, subscription: Dict):
        """Remove a tracked subscription"""
        with self._lock:
            if subscription in self._subscriptions:
                self._subscriptions.remove(subscription)

    # ========================================================================
    # PUBLIC SUBSCRIPTION METHODS
    # ========================================================================

    def subscribe_l2_book(self, coin: str) -> bool:
        """
        Subscribe to L2 order book updates for a coin

        Args:
            coin: Trading pair symbol (e.g., 'BTC', 'ETH')

        Returns:
            bool: True if subscription sent successfully
        """
        subscription = {"type": "l2Book", "coin": coin}
        success = self._send_subscription(subscription, subscribe=True)
        if success:
            self._add_subscription(subscription)
            cprint(f"Subscribed to L2 book: {coin}", "green")
            logger.info(f"Subscribed to L2 book for {coin}")
        return success

    def unsubscribe_l2_book(self, coin: str) -> bool:
        """Unsubscribe from L2 order book updates"""
        subscription = {"type": "l2Book", "coin": coin}
        success = self._send_subscription(subscription, subscribe=False)
        if success:
            self._remove_subscription(subscription)
            logger.info(f"Unsubscribed from L2 book for {coin}")
        return success

    def subscribe_trades(self, coin: str) -> bool:
        """
        Subscribe to trade updates for a coin

        Args:
            coin: Trading pair symbol (e.g., 'BTC', 'ETH')

        Returns:
            bool: True if subscription sent successfully
        """
        subscription = {"type": "trades", "coin": coin}
        success = self._send_subscription(subscription, subscribe=True)
        if success:
            self._add_subscription(subscription)
            cprint(f"Subscribed to trades: {coin}", "green")
            logger.info(f"Subscribed to trades for {coin}")
        return success

    def unsubscribe_trades(self, coin: str) -> bool:
        """Unsubscribe from trade updates"""
        subscription = {"type": "trades", "coin": coin}
        success = self._send_subscription(subscription, subscribe=False)
        if success:
            self._remove_subscription(subscription)
            logger.info(f"Unsubscribed from trades for {coin}")
        return success

    def subscribe_candles(self, coin: str, interval: str = "1m") -> bool:
        """
        Subscribe to candle updates for a coin

        Args:
            coin: Trading pair symbol (e.g., 'BTC', 'ETH')
            interval: Candle interval (e.g., '1m', '5m', '15m', '1h', '4h', '1d')

        Returns:
            bool: True if subscription sent successfully
        """
        subscription = {"type": "candle", "coin": coin, "interval": interval}
        success = self._send_subscription(subscription, subscribe=True)
        if success:
            self._add_subscription(subscription)
            cprint(f"Subscribed to {interval} candles: {coin}", "green")
            logger.info(f"Subscribed to {interval} candles for {coin}")
        return success

    def unsubscribe_candles(self, coin: str, interval: str = "1m") -> bool:
        """Unsubscribe from candle updates"""
        subscription = {"type": "candle", "coin": coin, "interval": interval}
        success = self._send_subscription(subscription, subscribe=False)
        if success:
            self._remove_subscription(subscription)
            logger.info(f"Unsubscribed from {interval} candles for {coin}")
        return success

    def subscribe_all_mids(self) -> bool:
        """
        Subscribe to all mid prices updates

        Returns:
            bool: True if subscription sent successfully
        """
        subscription = {"type": "allMids"}
        success = self._send_subscription(subscription, subscribe=True)
        if success:
            self._add_subscription(subscription)
            cprint("Subscribed to all mid prices", "green")
            logger.info("Subscribed to allMids")
        return success

    def unsubscribe_all_mids(self) -> bool:
        """Unsubscribe from all mid prices"""
        subscription = {"type": "allMids"}
        success = self._send_subscription(subscription, subscribe=False)
        if success:
            self._remove_subscription(subscription)
            logger.info("Unsubscribed from allMids")
        return success

    def subscribe_user_events(self, user_address: str) -> bool:
        """
        Subscribe to user events (fills, orders, etc.)

        Args:
            user_address: User's wallet address

        Returns:
            bool: True if subscription sent successfully
        """
        subscription = {"type": "userEvents", "user": user_address}
        success = self._send_subscription(subscription, subscribe=True)
        if success:
            self._add_subscription(subscription)
            cprint(f"Subscribed to user events: {user_address[:8]}...", "green")
            logger.info(f"Subscribed to user events for {user_address}")
        return success

    def unsubscribe_user_events(self, user_address: str) -> bool:
        """Unsubscribe from user events"""
        subscription = {"type": "userEvents", "user": user_address}
        success = self._send_subscription(subscription, subscribe=False)
        if success:
            self._remove_subscription(subscription)
            logger.info(f"Unsubscribed from user events for {user_address}")
        return success

    def subscribe_user_fills(self, user_address: str) -> bool:
        """
        Subscribe to user trade fills

        Args:
            user_address: User's wallet address

        Returns:
            bool: True if subscription sent successfully
        """
        subscription = {"type": "userFills", "user": user_address}
        success = self._send_subscription(subscription, subscribe=True)
        if success:
            self._add_subscription(subscription)
            cprint(f"Subscribed to user fills: {user_address[:8]}...", "green")
            logger.info(f"Subscribed to user fills for {user_address}")
        return success

    def unsubscribe_user_fills(self, user_address: str) -> bool:
        """Unsubscribe from user fills"""
        subscription = {"type": "userFills", "user": user_address}
        success = self._send_subscription(subscription, subscribe=False)
        if success:
            self._remove_subscription(subscription)
            logger.info(f"Unsubscribed from user fills for {user_address}")
        return success

    def subscribe_order_updates(self, user_address: str) -> bool:
        """
        Subscribe to order status updates

        Args:
            user_address: User's wallet address

        Returns:
            bool: True if subscription sent successfully
        """
        subscription = {"type": "orderUpdates", "user": user_address}
        success = self._send_subscription(subscription, subscribe=True)
        if success:
            self._add_subscription(subscription)
            cprint(f"Subscribed to order updates: {user_address[:8]}...", "green")
            logger.info(f"Subscribed to order updates for {user_address}")
        return success

    def unsubscribe_order_updates(self, user_address: str) -> bool:
        """Unsubscribe from order updates"""
        subscription = {"type": "orderUpdates", "user": user_address}
        success = self._send_subscription(subscription, subscribe=False)
        if success:
            self._remove_subscription(subscription)
            logger.info(f"Unsubscribed from order updates for {user_address}")
        return success

    # ========================================================================
    # CONNECTION MANAGEMENT
    # ========================================================================

    def close(self):
        """Close the WebSocket connection gracefully"""
        logger.info("Closing WebSocket connection...")
        cprint("Closing WebSocket connection...", "yellow")

        self._should_reconnect = False
        self._state = ConnectionState.CLOSED

        if self._ws:
            try:
                self._ws.close()
            except Exception as e:
                logger.error(f"Error closing WebSocket: {e}")

        # Wait for thread to finish
        if self._ws_thread and self._ws_thread.is_alive():
            self._ws_thread.join(timeout=5.0)

        cprint("WebSocket connection closed", "yellow")
        logger.info("WebSocket connection closed")

    def get_subscription_count(self) -> int:
        """Get the number of active subscriptions"""
        with self._lock:
            return len(self._subscriptions)

    def get_subscriptions(self) -> List[Dict]:
        """Get list of active subscriptions"""
        with self._lock:
            return self._subscriptions.copy()

    def get_last_message_time(self) -> Optional[datetime]:
        """Get the time of the last received message"""
        return self._last_message_time


# ============================================================================
# EXAMPLE USAGE AND TESTING
# ============================================================================

def _example_message_handler(data: Dict):
    """Example message handler for testing"""
    channel = data.get("channel", "unknown")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Channel: {channel}")

    if channel == "l2Book":
        book_data = data.get("data", {})
        coin = book_data.get("coin", "")
        levels = book_data.get("levels", [[], []])
        if levels[0] and levels[1]:
            best_bid = levels[0][0] if levels[0] else {"px": "N/A"}
            best_ask = levels[1][0] if levels[1] else {"px": "N/A"}
            print(f"  {coin}: Bid={best_bid.get('px', 'N/A')} | Ask={best_ask.get('px', 'N/A')}")

    elif channel == "trades":
        trades = data.get("data", [])
        for trade in trades[:3]:  # Show first 3 trades
            print(f"  Trade: {trade.get('coin')} {trade.get('side')} {trade.get('sz')} @ {trade.get('px')}")

    elif channel == "allMids":
        mids = data.get("data", {}).get("mids", {})
        print(f"  Received {len(mids)} mid prices")


def _example_error_handler(error: Exception):
    """Example error handler for testing"""
    cprint(f"Error received: {error}", "red")


def _example_connect_handler():
    """Example connect handler for testing"""
    cprint("Connected! Ready to receive data.", "green")


def _example_disconnect_handler(was_clean: bool):
    """Example disconnect handler for testing"""
    if was_clean:
        cprint("Disconnected cleanly", "yellow")
    else:
        cprint("Connection lost unexpectedly", "red")


def test_websocket():
    """Test the WebSocket client"""
    cprint("\n" + "=" * 60, "cyan")
    cprint("Moon Dev's Hyperliquid WebSocket Test", "cyan")
    cprint("=" * 60 + "\n", "cyan")

    # Create client with callbacks
    ws = HyperliquidWebSocket(
        on_message=_example_message_handler,
        on_error=_example_error_handler,
        on_connect=_example_connect_handler,
        on_disconnect=_example_disconnect_handler,
        auto_reconnect=True
    )

    try:
        # Connect
        ws.connect()

        # Wait for connection
        time.sleep(2)

        if not ws.is_connected:
            cprint("Failed to connect!", "red")
            return

        # Subscribe to some channels
        ws.subscribe_all_mids()
        ws.subscribe_l2_book("BTC")
        ws.subscribe_trades("ETH")

        cprint(f"\nActive subscriptions: {ws.get_subscription_count()}", "cyan")

        # Run for a while to receive messages
        cprint("\nReceiving messages for 30 seconds...\n", "cyan")
        time.sleep(30)

    except KeyboardInterrupt:
        cprint("\nInterrupted by user", "yellow")

    finally:
        # Clean up
        ws.close()
        cprint("\nTest complete!", "cyan")


if __name__ == "__main__":
    test_websocket()
