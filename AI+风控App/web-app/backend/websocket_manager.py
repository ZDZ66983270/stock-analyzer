"""
WebSocket Manager for Real-time Market Data Updates

Handles WebSocket connections and broadcasts market data updates to connected clients.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict
import json
import asyncio
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def broadcast(self, message: Dict):
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: Dictionary to send (will be JSON serialized)
        """
        if not self.active_connections:
            return
        
        json_message = json.dumps(message)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(json_message)
            except Exception as e:
                logger.error(f"Error sending to WebSocket: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_personal_message(self, message: Dict, websocket: WebSocket):
        """Send a message to a specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)


# Global instance
manager = ConnectionManager()


async def broadcast_market_update(symbol: str, market: str, data: Dict):
    """
    Broadcast a market data update to all connected clients.
    
    Args:
        symbol: Stock symbol
        market: Market code (US/HK/CN)
        data: Market data dictionary
    """
    message = {
        "type": "market_update",
        "symbol": symbol,
        "market": market,
        "data": data,
        "timestamp": data.get('date', '')
    }
    
    await manager.broadcast(message)
    logger.debug(f"Broadcasted update for {symbol} ({market})")
