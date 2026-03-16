# 💰 Financial Advisor Bot

A Streamlit-based financial advisor chatbot powered by Mistral AI. Get personalized financial advice on budgeting, investing, savings, and personal finance.

## Features

- 💬 Interactive chat interface powered by Mistral AI
- 📊 Real-time financial guidance
- 💾 Persistent chat history during session
- 🎨 Clean, modern UI with financial theme
- 🔐 Secure API key management

## Prerequisites

- Python 3.8+
- Mistral AI API key ([Get one here](https://console.mistral.ai/))

## Setup

### 1. Clone and Navigate to Project
```bash
cd financeapp
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Key

#### Option A: Environment Variable (Recommended)
```bash
cp .env.example .env
# Edit .env and add your MISTRAL_API_KEY
export MISTRAL_API_KEY="your_api_key_here"
```

#### Option B: Streamlit Secrets
1. Open Streamlit → Settings → Secrets
2. Add: `MISTRAL_API_KEY = "your_api_key_here"`

#### Option C: Sidebar Input
1. Run the app
2. Enter your API key in the sidebar when prompted

## Running the Application

```bash
streamlit run finaapp_py.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

1. Enter your financial questions in the chat input box
2. The bot will provide educational financial advice
3. Clear chat history using the sidebar button
4. View message count in the sidebar

## Project Structure

```
financeapp/
├── finaapp_py.py           # Main Streamlit application
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── .gitignore             # Git ignore rules
├── .streamlit/config.toml # Streamlit configuration
└── README.md              # This file
```

## Dependencies

- **streamlit** - Web app framework for data applications
- **mistralai** - Mistral AI API client

## Configuration

Customize the app behavior in `finaapp_py.py`:
- `MODEL`: Change the AI model (default: mistral-large-latest)
- `SYSTEM_PROMPT`: Modify the financial advisor persona
- `temperature` & `max_tokens`: Adjust response generation

## Disclaimer

⚠️ **Educational Use Only**

This chatbot provides educational information about personal finance. It is not a substitute for professional financial, investment, or legal advice. Always consult with qualified financial professionals before making important financial decisions.

## Troubleshooting

### API Key Not Found
- Ensure environment variable is set: `echo $MISTRAL_API_KEY`
- Or add the key via Streamlit secrets

### Import Errors
```bash
pip install --upgrade -r requirements.txt
```

### Streamlit Caching Issues
```bash
streamlit cache clear
streamlit run finaapp_py.py
```

## License

This project is open source and available under the MIT License.

## Support

For issues or questions:
1. Check Mistral AI documentation: https://docs.mistral.ai/
2. Streamlit documentation: https://docs.streamlit.io/
3. Create an issue in the repository

---

**Happy investing! 📈**
