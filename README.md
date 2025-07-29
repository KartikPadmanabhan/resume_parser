# Intelligent Resume Parser

An AI-powered resume parser that extracts structured data from resumes in multiple formats using the unstructured library and OpenAI GPT-4o with function calling.

## 🚀 Features

- **Multi-format Support**: PDF, DOCX, DOC, TXT, HTML resume parsing
- **AI-Powered Extraction**: GPT-4o with function calling for intelligent data extraction
- **Skill Inference**: Automatically infers related skills (e.g., Python from Streamlit usage)
- **Comprehensive Analysis**: Extracts contact info, skills, experience, education, certifications
- **Real-time UI**: Streamlit-based interface with progress indicators
- **Structured Output**: Canonical JSON schema format for consistent results

## 🏗️ Architecture

```
resume_parser/
├── src/
│   ├── models/           # Pydantic schema models
│   │   ├── schema.py     # Canonical JSON schema
│   │   └── resume_elements.py  # Document element models
│   ├── parsers/          # Document processing
│   │   ├── document_parser.py  # Unstructured integration
│   │   └── content_processor.py  # Section grouping
│   ├── agents/           # AI-powered extraction
│   │   └── gpt_extractor.py  # GPT-4o function calling
│   └── ui/               # Streamlit frontend
│       ├── streamlit_app.py  # Main UI
│       └── file_validator.py  # File validation
├── config/
│   └── settings.py       # Configuration management
├── tests/
│   └── sample_resumes/   # Test files
├── requirements.txt      # Dependencies
└── main.py              # Entry point
```

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd resume_parser
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. **Required Environment Variables**:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   DEBUG=false
   ```

## 🚀 Usage

1. **Start the application**:
   ```bash
   streamlit run main.py
   ```

2. **Open your browser** to `http://localhost:8501`

3. **Upload a resume** (PDF, DOCX, DOC, TXT, or HTML)

4. **Parse Document**: Extract raw elements and group into sections

5. **Extract with GPT-4o**: Generate structured JSON output

## 📊 Processing Pipeline

### Step 1: Document Parsing
- Uses `unstructured` library to extract elements
- Identifies titles, text, lists, tables, contact info
- Groups elements by document structure

### Step 2: Content Processing
- Classifies elements into resume sections
- Uses pattern matching for section detection
- Calculates confidence scores for classifications

### Step 3: GPT-4o Extraction
- Sends grouped content to GPT-4o with function calling
- Extracts structured data matching canonical schema
- Infers implicit skills and relationships
- Calculates experience metrics

## 🎯 Output Schema

The system outputs structured JSON matching this schema:

```json
{
  "contactInfo": {
    "fullName": "string",
    "firstName": "string",
    "lastName": "string", 
    "email": "string",
    "phone": "string",
    "location": {
      "city": "string",
      "state": "string",
      "country": "string"
    }
  },
  "summary": "string",
  "skills": [
    {
      "name": "string",
      "category": "string",
      "experienceInMonths": "integer",
      "lastUsed": "string (YYYY-MM-DD)"
    }
  ],
  "education": [...],
  "workExperience": [...],
  "certifications": [...],
  "experienceSummary": {
    "totalMonthsExperience": "integer",
    "monthsOfManagementExperience": "integer", 
    "currentManagementLevel": "string",
    "description": "string"
  },
  "parserMetadata": {...}
}
```

## 🧠 AI-Powered Features

### Skill Inference
The system automatically infers related skills:
- **Streamlit** → Python, Web Development, Data Visualization
- **React** → JavaScript, HTML, CSS, Frontend Development
- **AWS** → Cloud Computing, DevOps, Infrastructure
- **Docker** → Containerization, DevOps, Linux

### Experience Analysis
- Calculates total months of experience from job history
- Identifies management experience from roles and descriptions
- Determines current management level
- Provides comprehensive experience summary

## 🔧 Configuration

### Settings (`config/settings.py`)
- File upload limits (default: 10MB)
- Supported file formats
- OpenAI model configuration
- Processing timeouts

### Environment Variables
- `OPENAI_API_KEY`: Required for GPT-4o integration
- `DEBUG`: Enable debug mode for detailed error messages
- `OPENAI_MODEL`: Model to use (default: gpt-4o)
- `OPENAI_MAX_TOKENS`: Maximum tokens for responses
- `OPENAI_TEMPERATURE`: Model temperature for consistency

## 🧪 Testing

Test with the provided sample resume:
```bash
# Sample file located at:
tests/sample_resumes/sample_resume.txt
```

## 📝 Development

### Code Standards
- **Type hints**: Consistent throughout codebase
- **PEP8**: Python style guide compliance
- **Modular design**: Separate concerns across modules
- **Error handling**: Comprehensive exception management

### Adding New File Formats
1. Update `SUPPORTED_EXTENSIONS` in `config/settings.py`
2. Add format validation in `file_validator.py`
3. Test with unstructured library compatibility

### Extending Skill Inference
Add new mappings to `_build_skill_inference_database()` in `gpt_extractor.py`

## 🚨 Troubleshooting

### Common Issues

1. **OpenAI API Key Error**:
   - Ensure `OPENAI_API_KEY` is set in `.env`
   - Verify API key has sufficient credits

2. **File Upload Fails**:
   - Check file size (max 10MB)
   - Verify file format is supported
   - Ensure file is not corrupted

3. **Parsing Errors**:
   - Enable debug mode: `DEBUG=true`
   - Check file content is readable
   - Try with different file format

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review error messages in debug mode
- Ensure all dependencies are installed correctly
