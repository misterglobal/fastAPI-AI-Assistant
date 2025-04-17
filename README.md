# AI Phone Assistant API

A FastAPI-based backend for an AI-powered phone assistant capable of handling calls, SMS, and calendar functionalities.

## Features

- **AI-powered voice calls**: Handle incoming and outgoing calls with AI agents
- **SMS automation**: Respond to SMS messages with AI-generated responses
- **Calendar integration**: Synchronize with Google Calendar for appointment scheduling
- **Multi-tenancy**: Support for multiple organizations with separate configurations
- **Scalability**: Designed to handle 10+ concurrent calls per agent
- **Voice synthesis**: High-quality voice responses powered by ElevenLabs

## Technology Stack

- **FastAPI**: High-performance async web framework
- **Supabase**: Database and authentication
- **Twilio**: Phone call and SMS handling
- **OpenAI**: Natural language processing
- **ElevenLabs**: Text-to-speech synthesis
- **Google Calendar API**: Calendar integration

## Getting Started

### Prerequisites

- Python 3.8+
- Twilio account
- OpenAI API key
- ElevenLabs API key
- Google Cloud Platform account (for Calendar API)

### Installation

1. Clone the repository:



2. Install dependencies:



3. Set environment variables:



### Running the API



The API will be available at http://localhost:8000.

## API Documentation

API documentation is available at http://localhost:8000/docs or http://localhost:8000/redoc when the server is running.

## Configuring Agents

Agents can be configured through the `/api/v1/configuration/agents` endpoint. An agent configuration includes:

- Name
- Greeting and goodbye messages
- System prompt for the AI
- Voice ID for text-to-speech
- Business hours
- Phone number

## Performance Considerations

The system is designed to handle multiple concurrent calls efficiently:

- Each agent can handle 10+ concurrent calls
- Connection pooling ensures efficient resource usage
- Caching reduces API calls to external services
- Asynchronous processing enables high throughput

## License

This project is licensed under the MIT License - see the LICENSE file for details.