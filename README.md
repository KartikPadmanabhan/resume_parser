# Intelligent Resume Parser

An AI-powered resume parsing application that extracts structured information from resumes in multiple formats (PDF, DOCX, DOC, TXT, HTML) using OpenAI's GPT-4o model.

## 🚀 Features

- **Multi-format Support**: PDF, DOCX, DOC, TXT, HTML resume parsing
- **AI-Powered Extraction**: Uses OpenAI GPT-4o for intelligent information extraction
- **Structured Output**: Returns clean, structured JSON data
- **Skill Inference**: Automatically infers implicit skills from experience descriptions
- **Error Handling**: Comprehensive validation and error reporting
- **Token Tracking**: Monitors OpenAI API usage and costs
- **Web Interface**: User-friendly Streamlit web application

## 🛠️ Technology Stack

- **Backend**: Python 3.11
- **Web Framework**: Streamlit
- **AI/ML**: OpenAI GPT-4o
- **Document Processing**: Unstructured library
- **Data Validation**: Pydantic
- **Containerization**: Docker
- **Deployment**: Railway.app

## 📋 Prerequisites

- Python 3.11+
- OpenAI API Key
- Docker (for containerized deployment)

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd resume_parser
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set environment variables**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

5. **Run the application**
   ```bash
   streamlit run main.py
   ```

6. **Open your browser** to the URL provided by Streamlit

### Docker Deployment

1. **Build the Docker image**
   ```bash
   docker build -t resume-parser .
   ```

2. **Run the container**
   ```bash
   docker run -p 8080:8080 -e OPENAI_API_KEY="your-openai-api-key" resume-parser
   ```

3. **Access the application** at the URL provided by your deployment platform

### Railway Deployment

1. **Deploy to Railway**
   ```bash
   railway up
   ```

2. **Set environment variables in Railway dashboard**
   - `OPENAI_API_KEY`: Your OpenAI API key

3. **Access the application** at the Railway-provided URL

## 📁 Project Structure

```
resume_parser/
├── config/
│   ├── __init__.py
│   └── settings.py          # Application configuration
├── src/
│   ├── agents/
│   │   └── gpt_extractor.py # OpenAI GPT-4o integration
│   ├── models/
│   │   ├── resume_elements.py # Pydantic models
│   │   ├── schema.py         # Data schemas
│   │   └── token_usage.py    # Token tracking
│   ├── parsers/
│   │   ├── content_processor.py # Content processing
│   │   └── document_parser.py   # Document parsing
│   └── ui/
│       ├── file_validator.py    # File validation
│       └── streamlit_app.py     # Streamlit UI
├── tests/
│   └── sample_resumes/      # Test files
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
├── Procfile               # Railway deployment config
└── railway.json           # Railway configuration
```

## 🔧 Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_MODEL`: OpenAI model to use (default: gpt-4o)
- `MAX_FILE_SIZE_MB`: Maximum file size in MB (default: 10)
- `ENABLE_DEBUG_MODE`: Enable debug mode (default: false)

### Supported File Formats

- **PDF**: `.pdf`
- **Microsoft Word**: `.docx`, `.doc`
- **Text**: `.txt`
- **HTML**: `.html`

## 🧪 Testing

Run tests with sample resumes:

```bash
python -m pytest tests/
```

## 📊 Features

### Resume Parsing
- Extracts personal information, education, work experience, skills
- Handles multiple document formats
- Processes both explicit and implicit information

### AI-Powered Extraction
- Uses OpenAI GPT-4o for intelligent parsing
- Infers skills from job descriptions
- Handles various resume formats and layouts

### Web Interface
- File upload with drag-and-drop
- Real-time parsing results
- Error handling and validation
- Token usage tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues and questions:
- Check the documentation
- Review existing issues
- Create a new issue with detailed information

## 🔗 Links

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Streamlit Documentation](https://docs.streamlit.io)
- [Railway Documentation](https://docs.railway.app)
