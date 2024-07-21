# FastAPI-LLM-Classification
This is a FastAPI application that integrates with OpenAI's API & Instrcutor library for structured output. It's a good starting point and example for building any kind of Customer Support system where you need to classify incoming quieries into multiple categories. 

To make the system even more robust you coud add anVector DB (Chroma,Pinecone etc.) with s whole RAG pipeline that embeds the whole business knwoledge and is then connected to the FastAPI. 

## Features

- Integration with OpenAI API
- Custom API endpoints for language processing tasks
- Secure handling of API keys

## Prerequisites

- Python 3.7+
- FastAPI
- OpenAI Python library

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/marioyordanoff/LLM-Classification-FastAPI
   cd FastAPI-LLM-Classification
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables:
   Create a `.env` file in the root directory and add your API keys:
   ```
   OPENAI_API_KEY="your-openai-api-key"
   API_KEY="your-custom-api-key"
   ```

## Usage

1. Start the FastAPI server:
   ```
   uvicorn app.main:app --reload
   ```

   or if you have fastapi-cli

   ```
   fastapi dev main.py
   ```

3. Access the API documentation at `http://localhost:8000/docs`

4. Use the provided endpoints for various language processing tasks.

## API Documentation

### Authentication

All API endpoints require authentication using the `API_KEY` specified in your `.env` file. Include this key in the `X-API-Key` header of your requests.

### Endpoints

- `POST /generate`: Generate text using the OpenAI language model
- `POST /analyze`: Analyze text for sentiment, entities, or other NLP tasks
- `POST /summarize`: Summarize long pieces of text

For detailed information on request/response formats, please refer to the Swagger UI documentation available at `http://localhost:8000/docs` when the server is running.

## Security Notes

- Keep your `.env` file secure and never commit it to version control.
- Regularly rotate your API keys for enhanced security.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
