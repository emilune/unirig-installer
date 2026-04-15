# UniRig Installer V1

![Demo](demo.png)

## 📌 Description
UniRig Installer V5 is a graphical application designed to manage a UniRig / ComfyUI environment.

## ⚠️ Important — Initial UniRig installation
Before using this application, **UniRig must be installed via ComfyUI Manager**.

### Recommended steps
1. Open ComfyUI
2. Open **Manager**
3. Search for **"UniRig"**
4. Click **Install**
5. Restart ComfyUI

👉 This application does not perform the initial UniRig installation.

## ⚠️ Important — ComfyUI Portable
If you are using **ComfyUI Windows Portable**, do not run:

```bat
comfy-env install
```

This may use your **system Python** instead of ComfyUI’s **embedded Python**.

### ✅ Recommended method
1. Open a terminal in the **root folder** of ComfyUI portable
2. Run:

```bat
cd ComfyUI\custom_nodes\comfyui-unirig
..\..\python_embeded\Scripts\comfy-env.exe install
```

### 🧠 Explanation
- `python_embeded` is the Python used by ComfyUI portable
- `comfy-env.exe` must be run from this environment
- otherwise the installation may target the wrong Python

### ⚠️ Important
- run the command from the root folder of ComfyUI portable
- do not use the system `comfy-env`

## ⚙️ Requirements
- Windows
- Python 3.10 or higher installed

## 🚀 Launch
1. Open the application folder in a terminal
2. Run:

```bash
python app_en.py
```

## 🧠 Features
- Analysis of the installed ComfyUI environment
- Automatic patching
- Configuration restore
- Secure update of `comfy-env`
- UniRig environment installation
- Removal of `flash-attn`
- Installation of `torch_scatter`

## 🔧 Usage
### 1. Configuration
- Set the Python path
- Verify detected paths

### 2. Main actions
- **Analysis** → checks the environment
- **Patch** → applies fixes
- **Restore** → restores original state

### 3. Advanced actions
- **Update comfy-env** → installs or updates
- **Install UniRig Env** → runs the correct `comfy-env.exe` for the selected environment
- **Remove flash-attn** → cleans the configuration
- **Install torch_scatter** → installs a compatible version

## 🔒 Safety
Actions are executed in secure mode:
- no free shell commands
- controlled paths
- user confirmation
- logs displayed in the application

## 📝 Logs
All actions are displayed in the **Log** tab.

## 🙏 Credits
Thanks to the creators of UniRig and the ComfyUI community.

## ⚠️ Warning
This application modifies the Python environment.
Creating a backup before use is recommended.

## 👤 Author
Project initiated and developed by emilune
GitHub : https://github.com/emilune
With assistance from ChatGPT for technical problem-solving and automation.

## 🙏 Acknowledgements
* ComfyUI community * UniRig developers * Open-source ecosystem

