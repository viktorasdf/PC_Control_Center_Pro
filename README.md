# PC Control Center Pro

**Modern Windows PC monitoring, diagnostics and maintenance utility.**

PC Control Center Pro is a modern Windows desktop application designed to help users monitor system performance, inspect hardware, manage startup applications, run maintenance tools, and diagnose common PC issues from one convenient interface.

## 🚀 Version 2.0.0

**PC Control Center Pro 2.0.0** is the first public release of the project.

### ✨ Features

#### 📊 Monitoring Dashboard

* Real-time CPU monitoring
* Real-time GPU monitoring
* RAM usage monitoring
* Disk usage monitoring
* Circular performance gauges
* Real-time performance graph
* System information overview
* Visual system status indicators

#### 🛠️ System Tools

Access commonly used Windows system utilities from one interface.

* Windows system tools
* Maintenance utilities
* Security-related tools
* System management shortcuts

#### ⚡ Startup Manager

Manage applications that start with Windows.

* View startup applications
* Inspect startup entries
* Enable or disable startup items
* Startup analysis

#### 🧹 PC Maintenance

Tools for keeping Windows clean and responsive.

* System cleanup
* Temporary file cleanup
* Maintenance operations
* Quick optimization

> Some maintenance operations may require administrator privileges.

#### 🤖 AI Assistant & Diagnostics

Built-in diagnostic functionality helps analyze system conditions and identify potential problems.

The diagnostic system can evaluate:

* CPU load
* RAM usage
* Disk activity
* GPU activity
* System stability
* Detected performance problems

AI-related functionality may require an Internet connection.

#### 🌍 Multilingual Interface

The application currently supports:

* 🇷🇺 Russian
* 🇺🇦 Ukrainian
* 🇬🇧 English
* 🇩🇪 German
* 🇮🇹 Italian
* 🇪🇸 Spanish
* 🇫🇷 French

#### 🎨 Themes

* Dark theme
* Light theme

The interface is designed for a modern Windows desktop experience.

---

## 🖥️ System Requirements

### Minimum

* Windows 11
* 64-bit system
* Python is **not required** for the packaged Windows release

### Recommended

* Windows 11 64-bit
* Modern multi-core CPU
* At least 4 GB RAM
* Administrator privileges for some system maintenance operations

An Internet connection may be required for AI-related functionality.

---

## 📦 Download

The public Windows release is available from the project's GitHub Releases page.

### PC Control Center Pro 2.0.0

**Package:** `PC_Control_Center_Pro_2.0.zip`

The release is intended for **Windows 11 64-bit** systems.

---

## ▶️ Running from Source

If you want to run the project directly from Python:

```bash
python main.py
```

Install the required dependencies first:

```bash
pip install -r requirements.txt
```

The project uses Python and PySide6 for the desktop interface.

---

## 🔧 Project Structure

```text
PC_Control_Center_Pro/
│
├── app/
│   ├── core/
│   ├── pages/
│   ├── services/
│   └── ...
│
├── docs/
│
├── diagnose_qt_text.py
├── gpu_test.ps1
├── main.py
├── requirements.txt
├── run.bat
├── PC_Control_Center_Pro_2.0.spec
└── README.md
```

---

## 🔐 Security & Privacy

PC Control Center Pro is intended as a local Windows desktop utility.

Some features interact directly with Windows system components and may require elevated administrator privileges.

Users should review system operations before running maintenance or optimization functions and should keep important data backed up.

---

## 🚧 Development Status

**Current version: 2.0.0**

The project is actively evolving.

Future versions may include:

* Additional monitoring capabilities
* More diagnostic features
* Additional Windows utilities
* Further interface improvements
* Additional language support
* Performance improvements

---

## 🐛 Bug Reports & Suggestions

If you find a problem, have a feature request, or want to suggest an improvement, please open an **Issue** in this repository.

When reporting a problem, please include:

* Windows version
* Application version
* Description of the problem
* Steps to reproduce it
* Relevant error messages or screenshots

---

## 🤝 Contributing

Suggestions, bug reports, testing feedback, and improvements are welcome.

Please open an Issue or Pull Request to contribute to the project.

---

## ⭐ Support the Project

If you find **PC Control Center Pro** useful, consider giving the repository a ⭐ on GitHub.

Your feedback and support help the project continue to develop.

---

## 📌 Release

**PC Control Center Pro v2.0.0**

First public release — September 2026.

---

### Monitor. Diagnose. Maintain.

**One place for your Windows PC.**
