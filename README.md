# AI Text Rephrase 📝✨

An elegant desktop application that enhances your writing in real-time using Google's Gemini AI.

![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-brightgreen.svg)
![Python](https://img.shields.io/badge/python-3.11+-yellow.svg)

## ✨ Features

- **Instant Text Enhancement**: Improve your writing with a simple keyboard shortcut
- **Works Everywhere**: Enhance text in any application - emails, documents, browsers, chat apps
- **Customizable AI Instructions**: Define exactly how you want your text improved
- **Adjustable Creativity**: Control how creative the AI gets with your content
- **Minimal UI**: Sits quietly in your system tray until you need it
- **Privacy-Focused**: Your text is only processed when you explicitly request it

## 🚀 How It Works

1. **Copy text** or select text in any application
2. **Press the shortcut** (default: `Ctrl+Shift+H`)
3. **Watch the magic happen** as your text is automatically enhanced and pasted back

## 🛠️ Installation

### Option 1: Download the Installer
1. Download the latest installer from the master branch: [AI-Text-Rephraser-Installer.exe](https://github.com/itamar-shashar/AI-Text-Rephraser-app/blob/master/AI-Text-Rephraser-Installer.exe)
2. Run the installer and follow the prompts
3. Launch the app from your Start menu

### Option 2: Build from Source
```bash
# Clone the repository
git clone https://github.com/itamar-shashar/AI-Text-Rephraser-app.git
cd AI-Text-Rephraser-app

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python src/rephrase_app.py
```

## ⚙️ Configuration

Right-click the system tray icon to access settings:

- **API Key**: Enter your Google Gemini API key
- **Shortcut**: Customize your preferred keyboard combination
- **Rephrasing Instructions**: Define how you want text improved
- **Creativity Level**: Adjust how creative the AI should be
- **Model Selection**: Choose which Gemini model to use

## 🔑 API Key Setup

This application requires a Google Gemini API key:

1. Visit [Google AI Studio](https://aistudio.google.com/)
2. Create an account or sign in
3. Navigate to API keys and create a new key
4. Copy your API key and paste it in the app settings

## 💡 Use Cases

- **Professional Communication**: Enhance emails and business correspondence
- **Academic Writing**: Improve essays and research papers
- **Content Creation**: Polish blog posts and social media content
- **Documentation**: Refine technical documentation and instructions
- **International Users**: Get help with English writing

## 📋 Requirements

- Windows 10 or newer
- Python 3.6+ (if building from source)
- Internet connection (for API communication)
- Google Gemini API key

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [Google Gemini AI](https://ai.google.dev/) for powering the text enhancement
- [Pystray](https://github.com/moses-palmer/pystray) for system tray functionality
- [Keyboard](https://github.com/boppreh/keyboard) for hotkey handling

---

Made with ❤️ by [Itamar Shashar](https://github.com/itamar-shashar) 
