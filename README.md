# Doc2MD Converter

A high-performance, secure web utility designed to convert educational documents into clean, AI-ready Markdown text. Specifically built for educators to streamline the creation of digital learning resources.

## 🚀 Features

- **Multi-Format Support**: Converts PDF, DOCX, and ODT files to Markdown.
- **AI-Ready Output**: Preserves document structure (headings, lists, tables) for optimal compatibility with LLMs like ChatGPT and Claude.
- **Multilingual UI**: Fully localized interface supporting 24 European languages.
- **Teacher-Centric Design**: Simple drag-and-drop interface with instant clipboard copying and file download options.
- **Privacy Focused**: Ephemeral file processing with zero data retention on the server.

## 🛠️ Tech Stack

- **Frontend**: HTML5, Tailwind CSS, Vanilla JavaScript (deployed on Amazon S3).
- **Backend**: Python Flask, hosted on Render.
- **Conversion Engines**: 
  - `PyMuPDF` for high-speed PDF text extraction.
  - `Pandoc` for sophisticated DOCX and ODT to GitHub Flavored Markdown (GFM) conversion.

## 🔒 Security & Performance

- **Domain Lockdown**: Restricted API access limited to authorized `kidmedia` domains (.gr, .eu, .net).
- **Resource Protection**: Hard limit of 30MB per file to ensure server stability.
- **Cold Start Mitigation**: Integrated "Silent Ping" logic to pre-warm the server container upon page load.
- **CORS Policy**: Strict Cross-Origin Resource Sharing configuration for secure browser-to-server communication.

## 📁 Project Structure

- `app.py`: Flask backend with conversion logic and security middleware.
- `pdf2md.html`: Single-page frontend application.
- `assets/`: UI components and branding assets.
- `requirements.txt`: Python dependencies.

## 📝 License

Proprietary Software - Developed for **Kidmedia.eu**
