# Enhanced Unstructured Parser

## Overview
This feature branch contains an enhanced resume parser that leverages the unstructured library's full capabilities for generic content extraction and markdown formatting.

## Key Features

### 🎯 Generic Content Classification
- **No hardcoded sections** - Works with any resume format
- **Spatial analysis** - Uses coordinate data for proper content positioning
- **Adaptive formatting** - Detects headers, content, bullet points dynamically

### 📝 Markdown Output
- **Section headers** (`##`) - Automatically detected based on formatting
- **Subsection headers** (`###`) - Short text ending with colon
- **Bold text** (`**`) - Company names and job titles
- **Italic text** (`*`) - Date ranges
- **Bullet points** (`•`) - Automatically detected and formatted
- **Page separators** (`---`) - For multi-page resumes

### 🔧 Content Detection
- **Bullet points** - Detects various bullet styles (•, -, *, e, ¢)
- **Company names** - Pattern-based detection
- **Job titles** - Common job title patterns
- **Date ranges** - YYYY-YYYY, YYYY-present patterns
- **Section headers** - Based on formatting, not keywords

## Files Added/Modified

### Core Parser
- `src/parsers/enhanced_unstructured_parser.py` - Main enhanced parser

### Testing
- `test_enhanced_parser.py` - Minimal test for the enhanced parser

## Usage

```python
from src.parsers.enhanced_unstructured_parser import EnhancedUnstructuredParser

parser = EnhancedUnstructuredParser()
result = parser.parse_resume_as_is(file_content, filename)
```

## Testing

```bash
python test_enhanced_parser.py
```

## Benefits

1. **Generic** - Works with any resume format
2. **Clean Output** - Proper markdown formatting for GPT processing
3. **Spatial Awareness** - Uses coordinate data for accurate content positioning
4. **No Dependencies** - No hardcoded sections or keywords
5. **Robust** - Handles various file formats and content types

## Integration

The enhanced parser can be integrated into the main pipeline by replacing the existing parser calls with the new `EnhancedUnstructuredParser`. 