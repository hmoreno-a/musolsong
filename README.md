# MUSOLSONG Project

The **MUSOLSONG** project consists of two main applications:  
- **musolsong-controller**  
- **musolsong-yamleditor**

---

## 🧩 musolsong-yamleditor

The **yamleditor** is a graphical tool for creating and editing YAML configuration files specifically designed for use with the **musolsong-controller** application.  
It allows you to configure calibration and observation modes with precise modulation parameters.

---

## ⚙️ musolsong-controller

The **controller** coordinates calibration and observation procedures between the **MUSOL** polarimeter and **SONG** spectrograph.  
Operational sequences are defined via YAML configuration files and executed through a **Python-based GUI application** for sequence management.
The **controller** can operate either in GUI mode (default) or CLI mode when given specific arguments.

---


## **Usage**
```bash
musolsong-controller [--sequence-yaml SEQUENCE_YAML] [--project-name PROJECT_NAME] [--project-number PROJECT_NUMBER] [--validate-only] [--verbose] [--help]
```
## **options**

**General**

| Option   | Alias | Description                     |
| -------- | ----- | ------------------------------- |
| `--help` | `-h`  | Show this help message and exit |

**CLI Mode Arguments**

| Option                            | Alias               | Description                                               |
| --------------------------------- | ------------------- | --------------------------------------------------------- |
| `--sequence-yaml SEQUENCE_YAML`   | —                   | Path to sequence YAML modulations file (enables CLI mode) |
| `--project-name PROJECT_NAME`     | `-n PROJECT_NAME`   | Project name (required for CLI mode)                      |
| `--project-number PROJECT_NUMBER` | `-p PROJECT_NUMBER` | Project number (required for CLI mode)                    |
| `--validate-only`                 | —                   | Only validate the YAML file without processing            |
| `--verbose`                       | `-v`                | Enable verbose output                                     |

  
**GUI Mode**

Run without any arguments to start the graphical interface

**Running in simulation mode**

To run in simulation mode where both the musolLib and the SONG server are simulated:
    First launch the SONG simulator software in a separated terminal:
```bash
        musolsong-songsimulator
```
    Once the simulator is up and running, start the controller by typing:
    
```bash
        USE_MUSOLLIB_SIMULATOR=1 musolsong-controller
```

---
## Examples

  **GUI Mode** 
```bash
    musolsong-controller
```
  **CLI Mode**
```bash   
    musolsong-controller --sequence-yaml config.yaml --project-name "My Project" --project-number 123
```
  **CLI Validate Only**
```bash
  
  musolsong-controller --sequence-yaml config.yaml -n "Test" -p 456 --validate-only
```
  **YAML Editor**
```bash
  
  musolsong-yamleditor
```
---

## 📁 Project Structure

```text
MUSOLSONG
├── musolsong               # Root directory
│   ├── controller          # GUI app for coordinating operations between MUSOL and SONG
│   └── yamleditor          # GUI app for creating/editing MUSOLSONG YAML configuration files designed for use with the MUSOLSONG Controller
├── pyproject.toml          # Info to create, install, and publish packages
└── README.md

