# Jain QA Agent

A specialized AI-powered question-answering system designed for the Jain community. This agent provides accurate information about Digambar Jain scriptures, Tirthankaras, and practices using ReAct-based reasoning with LangChain.

## Features

- 🧠 **Intelligent Question Answering**: Uses advanced language models to answer questions about Jain philosophy and scriptures
- 📚 **Knowledge Indexing**: Upload and index .txt files to expand the knowledge base
- 💬 **Interactive Chat Interface**: User-friendly Streamlit-based chatbot
- 🔐 **API Key Management**: Secure API key handling
- 🌐 **RESTful API**: FastAPI backend for document uploads and chat queries
- 🗣️ **Hindi Support**: Native support for Hindi-language responses using custom ReAct prompts
- 💾 **Vector Database**: FAISS-based vector store for efficient document retrieval

## Architecture

### Components

1. **Frontend** (`app.py`): Streamlit application for user interaction
2. **Backend** (`main.py`): FastAPI server handling document indexing and chat logic
3. **Vector Store**: FAISS index for semantic search over indexed documents
4. **LLM**:  Generative AI  for response generation

## Prerequisites

- Python 3.8+
- API Key
- Required dependencies (see `requirements.txt`)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd jain-qa-agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file for environment variables:
```bash
GOOGLE_API_KEY=your_api_key_here
```

## Usage

### Running the Application

1. **Start the FastAPI backend** (in one terminal):
```bash
python main.py
```

2. **Start the Streamlit frontend** (in another terminal):
```bash
streamlit run app.py
```

3. **Access the application**:
   - Open `http://localhost:8501` in your browser

### Uploading Documents

1. Navigate to the **"Admin: Knowledge Feed"** section in the left sidebar
2. Upload a `.txt` file containing Jain scriptures or knowledge
3. Click **"Index Document"** to add it to the knowledge base

### Asking Questions

1. Enter your Gemini API Key in the Settings
2. Type your question about Jain philosophy in the chat input
3. The agent will retrieve relevant information and provide an answer in Hindi/English

## API Endpoints

### POST `/upload`
Uploads and indexes a text document.

**Parameters:**
- `file`: Text file to index
- `x-api-key`: Gemini API key (header)

**Response:**
```json
{
  "message": "Document indexed successfully"
}
```

### POST `/chat`
Sends a query and returns an answer.

**Parameters:**
- `query`: User's question
- `session_id`: Session identifier (UUID)
- `x-api-key`: Gemini API key (header)

**Response:**
```json
{
  "answer": "Detailed answer about Jain philosophy"
}
```

## Configuration

- **Model**: Google Generative AI Gemini 2.5 Flash
- **Embeddings**: Text Embedding 004
- **Vector Store**: FAISS (`faiss_index_shared`)
- **Memory**: Conversation Buffer Memory for session management
- **Language**: Primarily Hindi with English support

## Project Structure

```
jain-qa-agent/
├── app.py              # Streamlit frontend
├── main.py             # FastAPI backend
├── requirements.txt    # Python dependencies
├── README.md           # Project documentation
├── .env                # Environment variables (not in repo)
└── faiss_index_shared/ # Vector store (generated at runtime)
```

## Technologies Used

- **Streamlit**: Web interface framework
- **FastAPI**: REST API framework
- **LangChain**: LLM orchestration and tools
- **FAISS**: Vector similarity search
- **Google Generative AI**: Language model and embeddings
- **Python-dotenv**: Environment variable management

## Future Enhancements

- Multi-language support for all Indian languages
- Advanced document parsing for structured content
- User authentication and preferences
- Feedback mechanism for continuous improvement
- Integration with additional knowledge sources

## License

[Specify your license here]

## Support

For questions or issues, please open an issue in the repository.
