from flask import Flask
from flask_socketio import SocketIO, emit
import logging
from main_agent import TodoAgent
import asyncio

class SocketIOServer:
    def __init__(self, port=3001, debug=True, ready_event=None):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'todo-socket-server'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.port = port
        self.debug = debug
        self.ready_event = ready_event
        self.agent = None
        
        # Register event handlers
        self.socketio.on('connect')(self.handle_connect)
        self.socketio.on('disconnect')(self.handle_disconnect)
        self.socketio.on('message')(self.handle_message)
        self.socketio.on('ask_agent')(self.handle_agent_request)

    def handle_connect(self):
        logging.info('Client connected')
        emit('connection_response', {'data': 'Connected successfully'})

    def handle_disconnect(self):
        logging.info('Client disconnected')

    def handle_message(self, data):
        logging.info(f'Server received: {data}')
        emit('message_response', {'data': f'Server received: {data}'})

    async def process_agent_request(self, message):
        """Process the request using the AI agent"""
        try:
            response = await self.agent.runagent(message)
            return response
        except Exception as e:
            logging.error(f"Error processing agent request: {str(e)}")
            return f"Error: {str(e)}"

    def handle_agent_request(self, data):
        """Handle requests to the AI agent"""
        if not self.agent:
            self.agent = TodoAgent()
            logging.info("AI Agent initialized")

        message = data.get('message', '')
        if not message:
            emit('agent_response', {'data': 'No message provided'})
            return

        logging.info(f'Processing agent request: {message}')
        # Create a new event loop for async processing
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            response = loop.run_until_complete(self.process_agent_request(message))
            emit('agent_response', {'data': response})
        finally:
            loop.close()

    def run(self):
        """Start the Socket.IO server"""
        logging.info(f"Starting Socket.IO server on port {self.port}")
        # Signal that the server is ready before starting it
        if self.ready_event:
            self.ready_event.set()
        # Start the server (this will block until the server is shut down)
        self.socketio.run(self.app, host='0.0.0.0', port=self.port, debug=False)

# if __name__ == '__main__':
#     socketio.run(app, host='0.0.0.0', port=3001, debug=True) 