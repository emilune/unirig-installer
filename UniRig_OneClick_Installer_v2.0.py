from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess

# Hide child console windows when packaged with PyInstaller --windowed on Windows.
# This keeps the installer UI clean while pip/git/comfy-env commands run.
if os.name == "nt":
    _CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    _subprocess_run_original = subprocess.run
    _subprocess_popen_original = subprocess.Popen

    def _subprocess_run_hidden(*args, **kwargs):
        kwargs.setdefault("creationflags", _CREATE_NO_WINDOW)
        return _subprocess_run_original(*args, **kwargs)

    def _subprocess_popen_hidden(*args, **kwargs):
        kwargs.setdefault("creationflags", _CREATE_NO_WINDOW)
        return _subprocess_popen_original(*args, **kwargs)

    subprocess.run = _subprocess_run_hidden
    subprocess.Popen = _subprocess_popen_hidden

import threading
import time
import socket
from dataclasses import asdict, dataclass
from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk
import tkinter.font as tkfont

import customtkinter as ctk

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

APP_NAME = "UniRig OneClick Installer"
APP_VERSION = "2.0"
CONFIG_FILE = "unirig_oneclick_config.json"
COMFY_ENV_VERSION = "0.2.61"
EMBEDDED_VALIDATED_RECOVERY_MATRIX = "cu128 / torch2.8 / cp311 / flash_attn 2.7.4"
HISTORICAL_TORCH27_HYPOTHESIS = "cu128 / torch2.7 / cp311 (historical test hypothesis, not force-enabled in current code)"

APP_ICON_PNG_B64 = """iVBORw0KGgoAAAANSUhEUgAAADgAAAA4CAYAAACohjseAAAXbElEQVR4nHWae7BnVXXnP2uf83vcd/e9/aRpGgI0dNOAWBFRFHnGoXBk1GAsVAKO0UKZBIMZnApBpQZnxARjxYowxiLRYUQeOkpFkwiDI8IgNNAP6G7obuj37dd93/t7nHP2XvPH3vv8TpOZU9Xdv/499tlrre/6ru9a+wgAqoKIAtyyUc/e8WLx8fmDu64q5g+fSdEdEgF1DkURAWMMqKKAqqKqGCP4S1BFBRUFBFRExDoFVRIRRAARDKDqXwsCTkFRFBQkfE+ddSLhd86vj98tiKQL9K/cs2jF7/yvs85q/uBbH5BNVZskvlDV5P1/x11HX37yloXdvxrOjm7HdSbB5eH7DnUOkXhnRYzxBjmHfweMkfB5eCO8VnXemOAkEIIDwndMcI+/HOrXdP4+6hwIiJiwHiiCJHWksYjaotMZPO19nZXrrr7vW7fxpbUiXVQl5aOPmNdV00vvnXrs0NPfv2Z+68OguZWkJmKMiJShQZL4UkESkLDJNKH3iYaNCwRjVR3OgkmkNCxsDxHBqYbfh+h4yHiERM+J8WjxVhK35WymLIxrPrNHF/Y81Wwd3n7rp2c/+bafHdRrPvgVOgJw6Tfm/vbg/77v5tnN/z2TvsU1IwiuQNWGG6v3XoClj6JHQflZiABoxVjKaDprEWPKCPj1YrS8Q1Q9jEWiE8LyJqSCU2+c9BzlUyREVkSL1rF8+JxP1JdffMsDz9656FPy0Yf0oi0/fejZiWfucUlzUaIux4jzHlT1y2g0gpAgAT4lFDXe4EQDlQBjypwVqUA4filu1imgPseR8l7RIxr2Ub20F2LvKFPDtifsootuT1ZfcsMl6d7N+26Z3/VLEZOitgtqg0c15I3zy4u3UIPhJWwDZFQLel7wEIvwLN/3C3jY+V8GKPTWVFWcI6zpCczf2hviXJkAPsoaQoyPsI9yysLuX3L8lEtuSafHd76nO7nbg9wVYUM+ciU88TCIHtYSTn4jxkjYiJRQ8xtWcN45RkyZn0CZQ6gEo2z4TDAS7kEMmKDa+xxcIBlvkIj2HOIcIjXTndpF69hrF6dFe3qZzWYRk4iJmwpbiTmBeEKImAcHCnlRBIqPICmTEwCTJJhA775o9NYRlRBYTzLReZiELLdhibJ6hf87UO/Q6FQfAr8fD2lBJRGXzZO3JpemLuumavOA4VAGoIykc85vqaRnD6c8zxhdtAiTmMpmKOEowMJCi9wWJCYJXo8lwuCcLfPR26aoCNrpMDDcT9JoltEj5LI6hxihyDLm59tVt/r9lmVJcM6CK5JU1eKcxRhXht7vU5FKrkVvGWOYmpri9ls/w5/e+nm63YIkSXo3Eyispb+vwS/++Ulu/OxtDA0P46wLXo9UFfIxsCBi6M7Nc+p73sX6L/xXWgsJgkGd52dnQ4rUaszvOcDmr9+IkQwwZY1VVcQE0aAOVaspLtzI2RKeLia20Ks9eLKxFmqJ8KFr/y1jY2N0ujFCPWcU1tLXrLGwsEDebiHDw1hnQYzfdPRiSGNVhcTgsjaDF13JrvYqOscKxCSoCs4CTnGFg2bC7O69dOcnaQ4OApaSYQlOMAZwOGtJnbMhvIriFYl/7e/eM9CTSLebsWL5Ek45ZTXdrsVZi3Px9/6yhTfw6d88g1o94eY+XzQij5jmaEE60CRdfjazE4rYDM09/F1Reg7SfrpvPIPLZnE6WDKwCWVKQ7DUeTZOCeUAdUjIk0gUTiNvBb2ZJHS6Xc5eeyZLl46xsNDFJLHA90pUmqZ0uzmbt7yKaTSwtihZDwUjUhoWJZjNHP0rllCMnE73uCPF4JzxESwcagHrYdV6YyMY0+OHQFShboA6nDpwllRdMCqQSlncK5dWoqPdLhecvwERwTpXqop4OVWazTp79+zhjT37aTQbOBtroZSwdyihxAJC0ekwdPIasmSMotNFE/Gk6ZSi8P8aSbFTLeyRbdTqzbJGU4qRarnyoTcueJdI1aUnonHgnBfaThUMnH/eht7n9PSnAtZa0lTYtn07c5NTpEnSEwzq4ezLQiX/EFyR0TjtHFptwWUWm4HNFJsprvARttToHH4TN38AkzbBuXJtX9Zs+X/nHM46Ug/LqCRiJGNUesUcIM9yBocHWb9+HXkRRXH0R0+JCLBx40se9kZwVql6zUX9GB2IwyRCevIGZmbAFV4goIorfC65wkFd6OzbjNg5kKFSJUW2dyF6ZWcikEZ0Kb4sRIaTauFEMSJ0sy7rz1zDKatPodPJqOrDiAJfg+DFl14GUy/hbUK7F3MmigPFs2NtZBgzto5iDsQZbBGi7PzvsOAyyPc8R5KG2hvWczH3KtoHQJ0TE9VKT175/s7Dkh68RLDtDuvXncXw8AB5npebdIFtnSppWuf4xBRbXt2OaTZL2JfFXHsqydctg81yBk5ahfadSj7fxeWKzR22UJz1UHXOkE93KY5uQur90aMlQRK5PjTm+HRRU2U3vwcXtKELmC4/AJtzwfnn9ohCe5Hzuao0mjV27trFoYPj1BuNMul9iagQXQw4gss7DJy6lnanH9vu4nJBc7DdkIOZQ6lTTOxH5/dCUi/zjarDIhZdT7ynrlTgPSatEkzUnVbANOqcf/555EX8PGw+RLCwjloKW7duxWVd0uHUM22ATlUlob6HUxFQS+3k88r8y5zvPf3eBFdY0jSlOLINimmQZcFAevJQNapJVB0SUJeqtZFDKjo5bijKMyHPCxaPLeKMM86g3ck9Y8YyEaEfaPv5F14Mia4lArTnMdRImQqokDZTdPE62tOA9QYJxrdNTnHWUeSQH3oRERvUkC0DETs0Xxe9EHYhsqEOhmQNit4bHBnJL5F3upy2/gyWLVtOt5uVzW/ssnEgJmGhlbN16ytgGlgb+0kpmdhr0Ji9BpsXNEeX4gbPIDuWkTrKuuwCk6oT3LylOPISJqkFWVk1rzQz7MrfyRU5xsVaEnu9UA8j7IjUm3U4d8M6mn1Nr0wC5GItc6rUanUOHDjIazt3Y5oND5Wy5EQaCI7xBI3NutRXrKZVLEPbHTSQStF1uMzhckWp4+aOoLM7kLS/zPkyn8MLDQomxAdRMFGGVbv0uOleAfU8/fYLzu85LjJuuIG1lnq9xrZtrzI3NUm9Xn9L5EKqBOP8e75taqxaR2eugeYFNlO0ALW+fGhhQRrY49shO4qkzV7QFJz26niptlT9+16Llj4tcySyZFTEhbUkfX2cu+Fc2h2f3J6XKnBwSpoKG198EdRiTBIkmvZqZDlMCmXDgUkUs/J8utNAYbGFVNHm1U+R4I5uQiRHMV6wl3uMANXeWKNkV0g1QkhDTENUIsmICHm3y6qVy1iz5jQ6nS5R3PbmIv4mWa68/PJmoF5Gv/RbYLBemRecc6QD/dB/Fp0DGYka1MZUCXmtDpECndwESZ3Y//VUVsi6OBGI9gTSMyKVvHCx6Pe8I0bQLGPtGaczsniULMuIMxnn4h+HMSmTk1Ns2/Ea1JqhjupboFNFt2ALR31sGTmnYBc6aK5gQ7lSh+JQTdD2FMzvgHSACDENCqskw9h+xdCrLxepK7JekHv6x98kjvhcxoZz1pGmdYpiDhFTMq1znp4Hmv3s3PU6Bw+Mk9SbFfhIaLdCEoYNOknAdqitXEunM4rYaTRRiq7CQoHkARpDg0j+JpofRur9IZnEj1CiYq+kF+qndnF4nLoi6xkWM0QrWwu5eN5555EXttfl+9kfzilFYUnTGlu3bsZ2Z2k2h3we0Euncn31xT0OgGsrzmN2LkXFoseUlSv66b9sEB2DomXJ36wz/fhvaXfmYHAJLu+AWp9zEs5IAupMgKvEcYizpBhD5NWyGMdjE5S8sPSNDLN+/TknCuzSGYp1vky8sPHFHv7D/FKlF0nPNQ4woIJp1ElGNtA9ljMwnbPqxhW0L5rh4P/5J4qd42hfg4Erz2Ho4ksxX7mY1u790NeEvFPmm0rMvwrplEZbUsFvJo714nQ6IImi3eH0taeyatVqut1OiGpPmTgHRgytdoutW7aANAPBREBKpdQEBYPv0uuLx8j61lI/NMWq/7SMPfo02e/9iNHRVdTWn0p3YprZe7/N7KXD9N/1AOldf0z++itIowZxFKK95q5USjE3VUm9Eok+rmZNYLu8zfp1Z9E/OMLk5BS1WhoIhBKitbTG8eNHeXPvXqg1vASLbiqZPIySJQGTQOZorjqNYmIxo1en7Ku/jFz7fc74y5uZuOJkjmzaytDqC+gv/oDOJz9Ea/rrpNd/GfnP10PFgVLtKkobeghMqVwaflAehgmAZe2ZZ5TjAFeBg6ofW9STlPHxw8xMz5Ckfb1oSfVmoVKg3kgtqC1ZC3lK630ZnVsf5eQ/v4F9GxRz9Sc4uzbIjjd2wU2fIL3nYeRz12LP+Qic/354/mFoNlBre3leKVuRAFEwnokqTWKg16oWWrFihZ9LVkqDb48cznqaXphfwGVFODihzFWNlkVq1wCotMbg6nfSXqLMj+8lnXFMXHYW7ua7ePibd/CT7Y9z7z13IQ98k+L5HaQXfgg2PY0ueTvxPCqWgoiYslAEYeHUYUrBUuq7EwkEhIGBAQprPZmEZti63rA1y3JGFw9R62+GfA/RqxxzxcukNVy3YOm6dfSf/C5axTQcbeOGGrT3zZJOHWP1287kA7NgvnAdzz7xCOftPUL+xjRJMYPYwaDVI22GfOulYECJHwCbWC+ivkCj5IlmOqwN8izMGq0DaxXrHIih3e5w6qmn8zunrcF1OiRpEmmKskkDklodGw5j3nH9rUxMNDALU2h9BJ05RHJ0gE4ywLHtWzhJ4NbtXb7x9st48LvX8ScX5xRzo+j4HpIkDrHiVI8wm3UVMvPGGK0YEi0viT3k4PTUpB8TWkdhHda60linSmFzMH186c++iNoWnXZGkiSkaUItTUiSFMWQzczRcMJn7/wvZMMXURTzmJlZKBYjoyPIP/4U1tzE8UOHWGMgKYQfv5lx+fGES+//ax67+6OM7vs5dq5FmoTAqOXERr1X9J2zoass63zvSz2BJezevfst0izmoW9GRQwTk1NcftW13Pff/pbVy4fpzs3QmZqiPTlJd26Ovprh9666iq/d/wOSsz/I1LFJBkcSP1/5zVa4+vPIlh/Btr/nwNEOqx3YltLvDMfnHB96ueA3F53Cv/zyW1xz+RUUk4dCFpiy/mn1rxDJNJ45RERVZIw/oaHB8y+8QGthziv5t7ZVYdZijGH8yARXvv863n3xZWx84TkOHDiIdcrYkmWcdNoGZMk6thx1TI5PsKjPMNOypGNLKV7YiKgi/+5+ePB69rz+EucI0IUCJXF+Gv7NbTlPLDmdv3n4IS7/9j188e5v4KyjNtBPUeRlN+GP0CRo0UC1FU1VvnbWYfoGePXVrby+YwunnXkB7dZ8OK4Oa7nyeQiMMRw+epwkbfCOi6/hotRgnTDbgf2THQ6OT+GyhMFGwnTX0UwcjTp0TjoX3fg4bvkqOPNW3jz6NJflDooEjXoXpWGErYe6XDZu+Pof3c6Tl7ybWz/3H9iyYxvp4FJ/JlGmYJBv5Rl3leoqV5om2DzjB//wPYYGm3S6OU7Vk4x1gVkVp4JzipgEawsmJiYZHz/GwfFjHJ+YgLzNQF2oGaVhlP4UmjWh2Uyojy5CTnsP7vgR2PV99r25kaFuB2yC64JkPpp5B9JCMJnyH3/d5mv97+U7//QrbvvMTRTzx7FZHkR2VDiCKU9uY4FQreSi79ST5iiPPvYwzz/7JKNjS+h0umVOqvrhk7W21+ko/okKYwKLSnlekBror0N/TRhowGBTGBhKSVefDae8HbLtHDq0j9rscQYRbMuiHYWOQtviOop2lL7U8MTOFle9MMjqL97Pd777XZYvHfLzGokPNViMmDD67tFprwMPpQEjOJdy259+ns78EQYGhul2ut4BTnFWKYpwHqD+vaJQnPNRjcOnRJSaOBItaCSOoSYM1XNGVqyk3phHN90Jbp7pliOfOMRyA7QV6SjaVmgrdMBlQntWoKhTcynf2wEXfuoG7v7qnbjOTDivBHUFaalt1JeKsgHWHmydU0x9gL1793PTDdfxdw88xOjYSo4dP0YSoySCOoIACJFVCcNhP/jFeW2YAKnCcF8f+ZpTmH75KVoP/3t0epykbwm2fZjZwwdYNQa7WwqJIgqJgMXRSAw3nmr53aEOY+0DTO98ie/e8gK/+JenkPoA1uaRIDT1yj+2+JUnjQJPStSg6kiai9m8eQsf/uBVfO3rf82F734/UzMLtBbmKceDAfKOcARgvXHO+pIlGAb7+klHRugcn2Tnj/+CPT/9JlhB6iMIBeCYOHKQ1cuBBYdpQG79IU5aB5c5PnZJysN3fIoHHn2cTh4rQR/SHAwiJxQRdUUvcYjsE0tFT6OCF9amMcL+A4f55Md/nztu/yMO7XuVxYsGGR1dQv/AEGmtgTEpiRiMSUjTlEa9yeDgMEuWLmVsbDFF+yjP/uSveOS2S3jjsbuBGtT68cNcnyvjB/axuuYh6jIYcso7h6CYU/LM8ie/qXHZ73+WrjXUm4up9Y1hmuHMQnqWpCc8N6dxWhW+E+pi2T6JwalF6gPgHI88/EMee/RR3nHhhbznvZdx9vpzWbZyNc2+EUxSw1lHN+syOTPL+OFDvLbjVTa/9DyvbX6e7sIk0EDqY5VRSVRRCXv37+fCPjBWsHNw75Vw1Ukd3vHDPiZtwZbtc+z8wNV84XOf5t5v30fat8zvrTQmGOji7CGI5Nh2VK+yI9AwJnCKipA0FmGLgt8+9wy/fe4ZABrNQfr7+6k3Glhr6XYzWgstbNGqrNiHaYyGc8IgjEuPClBn774DXJN2cVOOv/rYIEd+/mW+9Oom/vL2n/KHD06RDgt3/3yeH//hl/nZL55g154jmFqjMppRUBGjiPVpr5VSGDyqVcEWLxM2ZLxwTlJMYxFJYxGmNky3q0xNznFk/CjHjx5nbmYB6wymPkLSGMU0FiO1hq+ZyAlpoGXjmjJ+9Bj53DQ3XzbM6t0PcsdX7+KhR3/GyL7/yb9ZP0IxU9Cab/GtTcv58p1fBdtCwhOQZQhFraE+dNTUmpxQ/KKJlclYOcmCwJpJGByZ0PiCYpBaHak3kXq//1NrQJLiMFjnzxs0sm6ckMZzfvVHX1KrsffgEdbUp/jw4HPc+OnPYJI+RGrc8Rdf4ou/O02fpNQa8Itfj3N05R/w8es/hm1PeVZXVUmbJOngESODq36dDqwCLVw1TtG7PfxWiSiME014wlB8UY9PH/a0e4SclClwInGd6NLyMUojdLqOmz7xEa77yLW0Whakhqn188q213j60W/wZ1eMkO/v8sF3LuLM4Slm5jv+uRpAXeaS/pVIuvRXMnTdb9+lO/7HM52d/+AKGolUxXfc7ltlXKWMVAcvGntJOTH65bn/W2wrD2Yi0ZXTugCzbA5IkFqj5AbB0axb/v5HT9Bd/C7cnse45+47eHX7TkxzDKeooesG1nxY2v1XXCQAI1f+8D637yefXXjz8cwlwzV/yxMjVv6j/8paotCTKBpK87VkNf9RaUklt6VikgYiq8xwYhMbSM6I4LIF1p61lvPPW8cjjzwCJJjmIpyKUszlw6uvqBcj7/ub1ubb/1jgy2bNA1+pT37v/n/k8BOXdw49RZ4XFknj48zVQkJU6RWzY/x60Su/KZUNa0VE6IkR/n+5rDyN1TLW3gEBYfk8kCO1EUWMqss1SZNkcNV7sX3v/uf5ztuu5YIHCsEPupXrXqkPHt74NZnedLOd2tJfzO/HZvOgRQU+PXOqDwCV5xhw4sOuUEIr3OX/07RUe7UYusrrSgPrF9GSnBwGk/aTDqykvmjDgmus/c785vk/h69mVJ5JDr+E2lVPbehr7fskrQNXFvnUGnFZP4iKBLGpDjGJ9nLLSeweQq6pqvNmmvDEoD9u1hMHUIK6QsL5R6jyWmZ0mLmoqkXESKXR8/FXDdqv3jbpwJuSLn1yIV/5IDtueKVq0/8FxkgWo4/bwyMAAAAASUVORK5CYII="""
APP_FOOTER = "UniRig OneClick Installer v2.0  ·  © 2025 Emilune  ·  Powered by UniRig (PozzettiAndrea)"

BG = "#D7DEE8"
SHELL = "#E7ECF3"
CARD = "#FBFCFE"
CARD_SOFT = "#F7F9FC"
BORDER = "#C9D3E0"
TEXT = "#162336"
MUTED = "#6B7A90"
TITLE = "#071A33"
SECTION = "#233C86"
PURPLE_TINT = "#E3D9FB"
PURPLE_TINT_HOVER = "#D5C6FA"
JOURNAL_BG = "#F5F7FA"
GREEN_TXT = "#18864B"
ORANGE_TXT = "#C47A16"
RED_TXT = "#B54747"
BLUE = "#2F6FED"
BLUE_HOVER = "#255AD1"
ONECLICK = "#F6DDE4"
ONECLICK_HOVER = "#EDD1D9"

LANGS = {
    "fr": {
        "title": "UniRig OneClick Installer",
        "subtitle": "",
        "info": "Infos",
        "configuration": "CONFIGURATION",
        "analysis": "ANALYSE",
        "journal": "JOURNAL",
        "advanced": "OUTILS AVANCÉS",
        "comfy_path": "Chemin ComfyUI",
        "unirig_path": "Chemin UniRig",
        "python_path": "Chemin Python",
        "browse": "Parcourir",
        "analyze": "Analyser",
        "install_unirig_btn": "Installer UniRig",
        "install_unirig_running": "Téléchargement et installation des nodes UniRig...",
        "button_working": "Installation...",
        "install_unirig_done": "Nodes UniRig téléchargés et installés dans custom_nodes",
        "install_unirig_exists": "Les nodes UniRig sont déjà présents dans ce ComfyUI",
        "install_unirig_failed": "Échec du téléchargement / installation des nodes UniRig",
        "helper": "Sélectionnez le dossier ComfyUI (celui contenant main.py)",
        "about_title": "À propos de UniRig OneClick Installer",
        "about_body": """Cette application valide, répare et finalise l’installation de UniRig dans ComfyUI.

        Version 2.0

        Utilisation recommandée :
        1. Installer UniRig dans ComfyUI
        2. Lancer UniRig OneClick Installer
        3. Cliquer sur OneClick Install
        4. Exécuter un workflow UniRig dans ComfyUI

        Important :
        ComfyUI doit être lancé en mode administrateur
        pour que les nodes UniRig s’affichent correctement
        et que les workflows fonctionnent.

        Ce que fait l’application :
        • détecte votre configuration ComfyUI et Python
        • bloque les cas incompatibles avant installation
        • met à jour comfy-env si nécessaire
        • nettoie les anciens environnements UniRig
        • lance comfy-env install automatiquement
        • applique les correctifs nécessaires
        """,
        "analysis_done": "Analyse terminée",
        "next_step_prefix": "Étape suivante recommandée :",
        "next_step_clean": "Nettoyage de l’environnement",
        "next_step_install": "Lancer l’installation",
        "detected_comfy": "ComfyUI détecté",
        "detected_python": "Python détecté",
        "detected_env": "comfy-env détecté",
        "label_comfy": "ComfyUI",
        "label_python": "Python",
        "label_env": "comfy-env",
        "detected_old": "Ancien environnement détecté",
        "no_unirig_env": "Aucun environnement UniRig détecté",
        "unirig_installed": "UniRig installé",
        "install_ready_config": "Installation prête pour configuration",
        "env_ready": "Environnement UniRig installé",
        "save": "SAUVEGARDER",
        "analysis_running": "Analyse en cours...",
        "current_action": "Action actuelle :",
        "not_started": "Non démarré",
        "analysis_required": "Veuillez lancer l’analyse avant le one-click.",
        "clear": "EFFACER",
        "export_script": "Exporter le script UniRig",
        "export_script_desc": "Détection automatique de votre configuration",
        "export_json": "Exporter le workflow JSON",
        "export_json_desc": "Workflow d’installation complet",
        "browse_mesh_tool": "Parcourir Mesh",
        "browse_mesh_desc": "Copier un chemin mesh",
        "browse_output_tool": "Dossier Output",
        "browse_output_desc": "Copier un dossier export",
        "export": "Exporter",
        "oneclick": "OneClick Install",
        "progress_idle": "En attente",
        "progress_running": "Installation en cours...",
        "progress_update": "Mise à jour comfy-env...",
        "progress_cleanup": "Nettoyage de l’ancien environnement...",
        "progress_install": "Installation de l’environnement UniRig...",
        "progress_patch": "Application des correctifs...",
        "progress_done": "Installation terminée",
        "progress_error": "Installation incomplète",
        "popup_title": "Ancien environnement UniRig détecté",
        "popup_msg": "Des environnements UniRig existants ont été détectés.\nIls peuvent empêcher UniRig de fonctionner correctement.\n\nVoulez-vous les supprimer avant de reconstruire l’installation ?",
        "popup_yes": "Oui (recommandé)",
        "popup_no": "Non",
        "detect_done": "Analyse terminée",
        "updating_env": "Mise à jour comfy-env",
        "installing_env": "Installation env UniRig",
        "patching": "Correctifs",
        "script_generated": "Script généré",
        "install_done": "Installation terminée",
        "workflow_restart_hint": "Si le workflow UniRig ne fonctionne pas immédiatement,\nredémarrez ComfyUI.",
        "install_incomplete": "Installation incomplète",
        "env_deleted": "Environnements UniRig nettoyés",
        "env_skip": "L’environnement existant n’a pas été supprimé (peut provoquer des erreurs)",
        "script_saved": "Script enregistré",
        "json_saved": "Configuration enregistrée",
        "unirig_synced": "Chemin UniRig synchronisé avec le ComfyUI analysé",
        "unirig_missing": "UniRig introuvable dans ce ComfyUI",
        "version_label": "Version",
        "version_unknown": "Non détectée",
        "status_missing": "Non détecté",
        "log_placeholder": "Logs apparaîtront ici...",
        "env_detected": "Environnement détecté",
        "python_path_set": "Chemin Python renseigné",
        "custom_nodes_path_set": "Chemin custom_nodes renseigné",
        "unirig_path_set": "Chemin UniRig renseigné",
        "comfy_path_found": "ComfyUI détecté",
        "python_found": "Python détecté",
        "python_not_found": "Python non détecté",
        "comfy_env_found": "comfy-env détecté",
        "comfy_env_missing": "comfy-env non détecté",
        "env_type_found": "Type d’environnement détecté",
        "comfy_running_title": "ComfyUI en cours d’exécution",
        "comfy_running_msg": "ComfyUI semble être en cours d’exécution.\n\nAvant de continuer :\n\nAssurez-vous que ComfyUI est bien fermé.",
        "install_finished_admin_msg": "Installation terminée.\n\nImportant :\nOuvrez ComfyUI en mode administrateur.\n\nVous pouvez ensuite lancer votre workflow UniRig.",
        "comfy_running_ok": "OK",
    },
    "en": {
        "title": "UniRig OneClick Installer",
        "subtitle": "",
        "info": "Info",
        "configuration": "CONFIGURATION",
        "analysis": "ANALYSIS",
        "journal": "LOG",
        "advanced": "ADVANCED TOOLS",
        "comfy_path": "ComfyUI path",
        "unirig_path": "UniRig path",
        "python_path": "Python path",
        "browse": "Browse",
        "analyze": "Analyze",
        "install_unirig_btn": "Install UniRig",
        "install_unirig_running": "Downloading and installing UniRig nodes...",
        "button_working": "Installing...",
        "install_unirig_done": "UniRig nodes downloaded and installed into custom_nodes",
        "install_unirig_exists": "UniRig nodes are already present in this ComfyUI",
        "install_unirig_failed": "Failed to download / install UniRig nodes",
        "helper": "Select the ComfyUI folder (the one containing main.py)",
        "about_title": "About UniRig OneClick Installer",
        "about_body": "This application validates, repairs and finalizes UniRig installation inside ComfyUI.\n\nVersion 2.0\n\nRecommended use:\n1. Install UniRig in ComfyUI\n2. Launch UniRig OneClick Installer\n3. Click OneClick Install\n4. Run a UniRig workflow in ComfyUI\n\nWhat the application does:\n• detects your ComfyUI and Python setup\n• blocks incompatible cases before installation\n• updates comfy-env if needed\n• cleans old UniRig environments\n• runs comfy-env install automatically\n• applies required fixes\n\nCurrently validated compatibility:\n• ComfyUI embedded mode\n• ComfyUI venv mode\n• Python 3.12\n\nNot yet validated:\n• ComfyUI local / system Python mode\n\nKnown limitations:\n• Python 3.13 is not currently supported\n\nExpected result:\nAfter the one-click flow, a UniRig workflow should run without environment-related errors.",
        "analysis_done": "Analysis complete",
        "next_step_prefix": "Recommended next step:",
        "next_step_clean": "Clean environment",
        "next_step_install": "Launch installation",
        "detected_comfy": "ComfyUI detected",
        "detected_python": "Python detected",
        "detected_env": "comfy-env detected",
        "label_comfy": "ComfyUI",
        "label_python": "Python",
        "label_env": "comfy-env",
        "detected_old": "Old environment detected",
        "no_unirig_env": "No UniRig environment detected",
        "unirig_installed": "UniRig installed",
        "install_ready_config": "Installation ready for configuration",
        "env_ready": "UniRig environment installed",
        "save": "SAVE",
        "analysis_running": "Analysis in progress...",
        "current_action": "Current action:",
        "not_started": "Not started",
        "analysis_required": "Please run analysis before one-click.",
        "clear": "CLEAR",
        "export_script": "Export UniRig script",
        "export_script_desc": "Automatic detection of your configuration",
        "export_json": "Export workflow JSON",
        "export_json_desc": "Complete installation workflow",
        "browse_mesh_tool": "Browse Mesh",
        "browse_mesh_desc": "Copy mesh path",
        "browse_output_tool": "Output Folder",
        "browse_output_desc": "Copy export folder",
        "export": "Export",
        "oneclick": "OneClick Install",
        "progress_idle": "Waiting",
        "progress_running": "Installation in progress...",
        "progress_update": "Updating comfy-env...",
        "progress_cleanup": "Cleaning old environment...",
        "progress_install": "Installing UniRig environment...",
        "progress_patch": "Applying fixes...",
        "progress_done": "Installation completed",
        "progress_error": "Installation incomplete",
        "popup_title": "Old UniRig environment detected",
        "popup_msg": "Existing UniRig environments were detected.\nThey may prevent UniRig from working correctly.\n\nDo you want to delete them before rebuilding the installation?",
        "popup_yes": "Yes (recommended)",
        "popup_no": "No",
        "detect_done": "Analysis complete",
        "updating_env": "Updating comfy-env",
        "installing_env": "Installing UniRig env",
        "patching": "Applying fixes",
        "script_generated": "Script generated",
        "install_done": "Installation completed",
        "workflow_restart_hint": "If the UniRig workflow does not work immediately,\nrestart ComfyUI.",
        "install_incomplete": "Installation incomplete",
        "env_deleted": "Old UniRig environments removed",
        "env_skip": "Existing environment was not removed (may cause errors)",
        "script_saved": "Script saved",
        "json_saved": "Configuration saved",
        "unirig_synced": "UniRig path synchronized with analyzed ComfyUI",
        "unirig_missing": "UniRig not found in this ComfyUI",
        "version_label": "Version",
        "version_unknown": "Not detected",
        "status_missing": "Not detected",
        "log_placeholder": "Logs will appear here...",
        "env_detected": "Environment detected",
        "python_path_set": "Python path set",
        "custom_nodes_path_set": "custom_nodes path set",
        "unirig_path_set": "UniRig path set",
        "comfy_path_found": "ComfyUI detected",
        "python_found": "Python detected",
        "python_not_found": "Python not detected",
        "comfy_env_found": "comfy-env detected",
        "comfy_env_missing": "comfy-env not detected",
        "env_type_found": "Detected environment type",
        "comfy_running_title": "ComfyUI running",
        "comfy_running_msg": "ComfyUI seems to be running.\n\nBefore continuing:\n\nMake sure ComfyUI is closed.",
        "install_finished_admin_msg": "Installation completed.\n\nImportant:\nOpen ComfyUI as administrator.\n\nYou can then run your UniRig workflow.",
    },
    "cn": {
        "title": "UniRig OneClick Installer",
        "subtitle": "",
        "info": "信息",
        "configuration": "配置",
        "analysis": "分析",
        "journal": "日志",
        "advanced": "高级工具",
        "comfy_path": "ComfyUI 路径",
        "unirig_path": "UniRig 路径",
        "python_path": "Python 路径",
        "browse": "浏览",
        "analyze": "分析",
        "install_unirig_btn": "安装 UniRig",
        "install_unirig_running": "正在下载并安装 UniRig 节点...",
        "button_working": "安装中...",
        "install_unirig_done": "UniRig 节点已下载并安装到 custom_nodes",
        "install_unirig_exists": "此 ComfyUI 中已存在 UniRig 节点",
        "install_unirig_failed": "下载 / 安装 UniRig 节点失败",
        "helper": "请选择 ComfyUI 文件夹（包含 main.py）",
        "about_title": "关于 UniRig OneClick Installer",
        "about_body": "此应用用于验证、修复并完成 UniRig 在 ComfyUI 中的安装。\n\n建议使用顺序：\n1. 在 ComfyUI 中安装 UniRig\n2. 完全关闭 ComfyUI\n3. 启动本应用\n4. 点击 OneClick Install\n5. 重新打开 ComfyUI 并运行 UniRig workflow\n\n应用会自动：\n• 检测 ComfyUI 与 Python 配置\n• 在安装前阻止不兼容情况\n• 在需要时更新 comfy-env\n• 清理旧的 UniRig 环境\n• 自动执行 comfy-env install\n• 应用必要修复\n\n当前已验证兼容：\n• embedded 模式\n• venv 模式\n• Python 3.12\n\n尚未验证：\n• local / system Python 模式\n\n已知限制：\n• 暂不支持 Python 3.13\n\n预期结果：\n完成 one-click 后，可重新打开 ComfyUI，并运行 UniRig workflow，且不再出现环境相关错误。",
        "analysis_done": "分析完成",
        "next_step_prefix": "建议下一步：",
        "next_step_clean": "清理环境",
        "next_step_install": "启动安装",
        "detected_comfy": "检测到 ComfyUI",
        "detected_python": "检测到 Python",
        "detected_env": "检测到 comfy-env",
        "label_comfy": "ComfyUI",
        "label_python": "Python",
        "label_env": "comfy-env",
        "detected_old": "检测到旧环境",
        "no_unirig_env": "未检测到 UniRig 环境",
        "unirig_installed": "UniRig 已安装",
        "install_ready_config": "安装已准备好进行配置",
        "env_ready": "UniRig 环境已安装",
        "save": "保存",
        "analysis_running": "分析进行中...",
        "current_action": "当前操作：",
        "not_started": "未开始",
        "analysis_required": "请先运行分析，再执行一键安装。",
        "clear": "清空",
        "export_script": "导出 UniRig 脚本",
        "export_script_desc": "自动检测您的配置",
        "export_json": "导出 workflow JSON",
        "export_json_desc": "完整安装流程",
        "export": "导出",
        "oneclick": "一键安装",
        "progress_idle": "等待",
        "progress_running": "安装进行中...",
        "progress_update": "正在更新 comfy-env...",
        "progress_cleanup": "正在清理旧环境...",
        "progress_install": "正在安装 UniRig 环境...",
        "progress_patch": "正在应用修复...",
        "progress_done": "安装完成",
        "progress_error": "安装未完整完成",
        "popup_title": "检测到旧的 UniRig 环境",
        "popup_msg": "检测到现有 UniRig 环境。\n它们可能会阻止 UniRig 正常工作。\n\n是否在重建安装前删除它们？",
        "popup_yes": "是（推荐）",
        "popup_no": "否",
        "detect_done": "分析完成",
        "updating_env": "更新 comfy-env",
        "installing_env": "安装 UniRig 环境",
        "patching": "应用修复",
        "script_generated": "脚本已生成",
        "install_done": "安装完成",
        "workflow_restart_hint": "如果 UniRig 工作流未能立即运行，\n请重启 ComfyUI。",
        "install_incomplete": "安装未完整完成",
        "env_deleted": "已删除旧的 UniRig 环境",
        "env_skip": "现有环境未删除（可能导致错误）",
        "script_saved": "脚本已保存",
        "json_saved": "配置已保存",
        "unirig_synced": "UniRig 路径已与分析的 ComfyUI 同步",
        "unirig_missing": "此 ComfyUI 中未找到 UniRig",
        "version_label": "版本",
        "version_unknown": "未检测到",
        "status_missing": "未检测到",
        "log_placeholder": "日志会显示在这里...",
        "env_detected": "检测到环境",
        "python_path_set": "Python 路径",
        "custom_nodes_path_set": "custom_nodes 路径",
        "unirig_path_set": "UniRig 路径",
        "comfy_path_found": "检测到 ComfyUI",
        "python_found": "检测到 Python",
        "python_not_found": "未检测到 Python",
        "comfy_env_found": "检测到 comfy-env",
        "comfy_env_missing": "未检测到 comfy-env",
        "env_type_found": "检测到环境类型",
        "comfy_running_title": "ComfyUI 正在运行",
        "comfy_running_msg": "ComfyUI 似乎正在运行。\n\n继续之前：\n\n请确保 ComfyUI 已关闭。",
        "install_finished_admin_msg": "安装完成。\n\n重要：\n请以管理员身份打开 ComfyUI。\n\n然后即可运行 UniRig 工作流。",
        "comfy_running_ok": "确定",
    },
}


@dataclass
class InstallerConfig:
    comfyui_path: str = ""
    python_path: str = ""
    python_version: str = ""
    comfy_env_version: str = ""
    unirig_path: str = ""
    custom_nodes_path: str = ""
    env_mode: str = ""
    language: str = "fr"


def app_dir() -> Path:
    return Path(__file__).resolve().parent


def config_path() -> Path:
    return app_dir() / CONFIG_FILE


def normalize_path(value: str) -> str:
    value = (value or "").strip().strip('"')
    return os.path.normpath(value) if value else ""


def safe_run_capture(cmd, cwd=None) -> str:
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    return (result.stdout or result.stderr or "").strip()


def detect_python_version(python_path: str) -> str:
    if not python_path or not Path(python_path).exists():
        return ""
    output = safe_run_capture([python_path, "--version"])
    return output.replace("Python", "").strip() if output else ""


def detect_installed_comfy_env_version(python_path: str) -> str:
    if not python_path or not Path(python_path).exists():
        return ""
    output = safe_run_capture([python_path, "-m", "pip", "show", "comfy-env"])
    for line in output.splitlines():
        if line.lower().startswith("version:"):
            return line.split(":", 1)[1].strip()
    return ""


def is_valid_python_executable(python_path: str) -> bool:
    if not python_path:
        return False
    p = Path(normalize_path(python_path))
    return p.exists() and p.is_file() and p.name.lower().startswith("python") and p.suffix.lower() == ".exe"


def _candidate_unirig_dirs(custom_nodes_dir: Path):
    return [
        custom_nodes_dir / "ComfyUI-UniRig",
        custom_nodes_dir / "comfyui-unirig",
    ]


def _find_first_existing_unirig(custom_nodes_dirs):
    seen = set()
    for custom_nodes_dir in custom_nodes_dirs:
        if not custom_nodes_dir:
            continue
        custom_nodes_dir = Path(custom_nodes_dir)
        key = str(custom_nodes_dir).lower()
        if key in seen:
            continue
        seen.add(key)
        for candidate in _candidate_unirig_dirs(custom_nodes_dir):
            if candidate.exists():
                return str(candidate), str(custom_nodes_dir)
    return "", ""


def _local_documents_root():
    # Compatibility shim for older UX builds; returns the Desktop ComfyUI user root.
    return Path.home() / "Documents" / "ComfyUI"


def _local_documents_custom_nodes():
    # ComfyUI Local/Desktop keeps the core under resources\ComfyUI,
    # but the active runtime custom_nodes can live in Documents\ComfyUI.
    return Path.home() / "Documents" / "ComfyUI" / "custom_nodes"


def detect_environment(comfyui_path: str, manual_python_path: str = "", manual_unirig_path: str = "") -> dict:
    path = Path(normalize_path(comfyui_path))
    if not path.exists():
        raise FileNotFoundError(f"ComfyUI path not found: {path}")

    resource_custom_nodes = path / "custom_nodes"
    documents_custom_nodes = _local_documents_custom_nodes()

    candidates = [
        ("embedded", path / "python_embeded" / "python.exe"),
        ("embedded", path.parent / "python_embeded" / "python.exe"),
        ("venv", path / "venv" / "Scripts" / "python.exe"),
        ("venv", path.parent / "venv" / "Scripts" / "python.exe"),
        # ComfyUI Desktop Local: app core is in resources\ComfyUI,
        # but the active Python lives in Documents\ComfyUI\.venv.
        ("local", Path.home() / "Documents" / "ComfyUI" / ".venv" / "Scripts" / "python.exe"),
    ]
    python_path = ""
    env_mode = "local"
    for mode, candidate in candidates:
        if candidate.exists():
            python_path = str(candidate)
            env_mode = mode
            break

    normalized_manual_python = normalize_path(manual_python_path)
    if not python_path and is_valid_python_executable(normalized_manual_python):
        python_path = normalized_manual_python
        env_mode = "local"

    normalized_manual_unirig = normalize_path(manual_unirig_path)
    unirig = ""

    # IMPORTANT — ComfyUI Desktop/Local split:
    # - core ComfyUI lives under resources\ComfyUI
    # - active user custom_nodes live under Documents\ComfyUI\custom_nodes
    # Installing UniRig into resources\ComfyUI\custom_nodes makes Desktop/Local workflows load
    # as UNKNOWN/Missing Node Packs. Therefore local mode must target Documents by default.
    if env_mode == "local":
        custom_nodes = documents_custom_nodes
    else:
        custom_nodes = resource_custom_nodes

    # Preserve a manually-selected UniRig only if it belongs to the active runtime custom_nodes.
    # For Desktop/Local, ignore stale resources\custom_nodes selections and keep Documents as source of truth.
    if normalized_manual_unirig:
        manual_u = Path(normalized_manual_unirig)
        if manual_u.exists() and manual_u.is_dir():
            manual_parent = manual_u.parent.resolve()
            active_parent = custom_nodes.resolve()
            # Multi-config safety: keep a manual UniRig path only if it belongs
            # to the custom_nodes folder of the currently selected ComfyUI.
            # This prevents a previous Local/Desktop path from contaminating
            # Portable / Easy-Install / other tests.
            if manual_parent == active_parent:
                unirig = str(manual_u)
                custom_nodes = manual_u.parent

    if not unirig:
        if env_mode == "local":
            # Desktop/Local: search only the active user custom_nodes first and do not select resources by accident.
            search_dirs = [documents_custom_nodes]
        else:
            # Embedded / Portable / venv: never fall back to Documents\ComfyUI.
            # The selected ComfyUI owns its own custom_nodes folder.
            search_dirs = [resource_custom_nodes]
        found_unirig, found_custom_nodes = _find_first_existing_unirig(search_dirs)
        if found_unirig:
            unirig = found_unirig
            custom_nodes = Path(found_custom_nodes)

    python_version = detect_python_version(python_path)
    comfy_env_version = detect_installed_comfy_env_version(python_path)

    return {
        "comfyui_path": str(path),
        "custom_nodes_path": str(custom_nodes),
        "unirig_path": unirig,
        "python_path": python_path,
        "python_version": python_version,
        "comfy_env_version": comfy_env_version,
        "env_mode": env_mode,
    }

def detect_old_unirig_env(unirig_path: str):
    if not unirig_path:
        return []
    nodes_dir = Path(unirig_path) / "nodes"
    results = []
    if nodes_dir.exists():
        results.extend(p for p in nodes_dir.glob("_env_*") if p.exists())
        # Some environments may be created as links/junctions or live under nested folders.
        # Use a broader recursive pass as a safety net for Desktop/venv installs.
        try:
            results.extend(p for p in nodes_dir.rglob("_env_*") if p.exists())
        except Exception:
            pass
    unique = []
    seen = set()
    for p in results:
        key = str(p).lower()
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return sorted(unique)



def _external_env_root_bases():
    # comfy-env may use different cache roots depending on launch context / drive.
    # Cleaning all known roots prevents false "Found existing env, skipping install" states.
    bases = [Path(r"C:\ce"), Path(r"D:\ce"), Path(r"E:\ce")]
    unique = []
    seen = set()
    for base in bases:
        key = str(base).lower()
        if key not in seen:
            seen.add(key)
            unique.append(base)
    return unique


def detect_external_unirig_env_roots(base_dir: str = ""):
    bases = [Path(base_dir)] if base_dir else _external_env_root_bases()
    results = []
    for base in bases:
        if base.exists():
            results.extend(sorted(p for p in base.glob("_env_*") if p.exists()))
    return results

def remove_old_env(paths, log):
    for p in paths:
        log(f"Removing old env: {p}")
        real_env_root = None
        try:
            if not p.exists() and not p.is_symlink():
                log(f"Old env already absent, skip: {p}")
                continue
            try:
                resolved = p.resolve(strict=True)
                for parent in [resolved] + list(resolved.parents):
                    if parent.name.startswith("_env_"):
                        real_env_root = parent
                        break
            except Exception:
                pass
            try:
                p.unlink()
            except FileNotFoundError:
                log(f"Old env already absent, skip: {p}")
                continue
            except Exception:
                try:
                    subprocess.run(["cmd", "/c", "rmdir", str(p)], check=True, capture_output=True, text=True)
                except subprocess.CalledProcessError as e:
                    if not p.exists():
                        log(f"Old env already absent, skip: {p}")
                        continue
                    if p.is_dir():
                        shutil.rmtree(p)
                    else:
                        p.unlink()
                except FileNotFoundError:
                    log(f"Old env already absent, skip: {p}")
                    continue
            log(f"✔ Link removed: {p}")
            if real_env_root and real_env_root.exists():
                log(f"Removing real env root: {real_env_root}")
                shutil.rmtree(real_env_root, ignore_errors=False)
                log(f"✔ Real env root removed: {real_env_root}")
        except FileNotFoundError:
            log(f"Old env already absent, skip: {p}")
            continue
        except Exception as e:
            log(f"Failed to remove {p}: {e}")
            raise


def remove_external_unirig_env_roots(log, base_dir: str = ""):
    bases = [Path(base_dir)] if base_dir else _external_env_root_bases()
    removed = 0
    for base in bases:
        if not base.exists():
            log(f"External env root base not found, skip: {base}")
            continue
        found_here = 0
        for p in sorted(base.glob("_env_*")):
            try:
                log(f"Removing external env root: {p}")
                shutil.rmtree(p, ignore_errors=False)
                log(f"✔ External env root removed: {p}")
                removed += 1
                found_here += 1
            except FileNotFoundError:
                pass
            except Exception as e:
                log(f"Failed to remove external env root {p}: {e}")
                raise
        if found_here == 0:
            log(f"No external UniRig env roots found in: {base}")
    return removed

def force_cleanup_unirig_envs(unirig_path: str, log):
    current_envs = detect_old_unirig_env(unirig_path)
    if current_envs:
        log(f"Forced cleanup policy: removing {len(current_envs)} UniRig node env link(s)")
        remove_old_env(current_envs, log)
    else:
        log("Forced cleanup policy: no UniRig node env link found")
    removed_external = remove_external_unirig_env_roots(log)
    return len(current_envs), removed_external



# UNIRIG_PATCH_MODULE_LOCK_V1
PATCH_TEMPLATES = {
    'auto_rig.py': '# UNIRIG_AUTO_RIG_ENV_RUNNER_V4_FULL_PATH\n"""\nUniRigAutoRig - ENV RUNNER VERSION v4.\nRuns the heavy UniRig pipeline inside the comfy-env isolated Python and returns\nan absolute FBX path for the preview node.\n"""\n\nimport logging\nimport os\nimport sys\nimport time\nimport pickle\nimport subprocess\nimport tempfile\nfrom pathlib import Path\n\nlog = logging.getLogger("unirig")\n\n_WORKER_CODE = r\'\'\'\nimport os\nimport sys\nimport pickle\nimport traceback\nfrom pathlib import Path\n\n\ndef _main():\n    payload_path = Path(sys.argv[1])\n    result_path = Path(sys.argv[2])\n\n    with payload_path.open("rb") as f:\n        payload = pickle.load(f)\n\n    comfy_root = payload["comfy_root"]\n    custom_node_root = payload["custom_node_root"]\n    nodes_dir = payload["nodes_dir"]\n    temp_dir = payload["temp_dir"]\n    output_dir = payload["output_dir"]\n\n    for p in [nodes_dir, custom_node_root, comfy_root]:\n        if p and p not in sys.path:\n            sys.path.insert(0, p)\n\n    # Avoid conflict with ComfyUI\'s top-level nodes.py.\n    import types\n    nodes_pkg = types.ModuleType("nodes")\n    nodes_pkg.__path__ = [nodes_dir]\n    nodes_pkg.__file__ = str(Path(nodes_dir) / "__init__.py")\n    nodes_pkg.__package__ = "nodes"\n    sys.modules["nodes"] = nodes_pkg\n\n    os.environ.setdefault("PYTHONIOENCODING", "utf-8")\n    os.environ["UNIRIG_ENV_RUNNER"] = "1"\n\n    try:\n        import folder_paths\n        folder_paths.get_temp_directory = lambda: temp_dir\n        folder_paths.get_output_directory = lambda: output_dir\n    except Exception:\n        pass\n\n    try:\n        from nodes.skeleton_extraction import UniRigExtractSkeletonNew\n        from nodes.skinning import UniRigApplySkinningMLNew\n\n        trimesh_obj = payload["trimesh"]\n        model = payload["model"]\n        skeleton_template = payload["skeleton_template"]\n        fbx_name = payload["fbx_name"]\n        target_face_count = payload["target_face_count"]\n\n        skeleton_model = model["skeleton_model"]\n        skinning_model = model["skinning_model"]\n\n        for sub_model in (skeleton_model, skinning_model):\n            if "dtype" not in sub_model:\n                sub_model["dtype"] = model.get("dtype")\n            if "attn_backend" not in sub_model:\n                sub_model["attn_backend"] = model.get("attn_backend", "auto")\n\n        skeleton_extractor = UniRigExtractSkeletonNew()\n        normalized_mesh, skeleton, _texture_preview = skeleton_extractor.extract(\n            trimesh=trimesh_obj,\n            skeleton_model=skeleton_model,\n            seed=42,\n            skeleton_template=skeleton_template,\n            target_face_count=target_face_count,\n        )\n\n        skinning_applier = UniRigApplySkinningMLNew()\n        fbx_output_path, _texture_preview2 = skinning_applier.apply_skinning(\n            normalized_mesh=normalized_mesh,\n            skeleton=skeleton,\n            skinning_model=skinning_model,\n            fbx_name=fbx_name,\n            voxel_grid_size=196,\n            num_samples=32768,\n            vertex_samples=8192,\n            voxel_mask_power=0.5,\n        )\n\n        if os.path.isabs(str(fbx_output_path)):\n            fbx_full_path = str(fbx_output_path)\n        else:\n            fbx_full_path = os.path.join(output_dir, str(fbx_output_path))\n\n        result = {"ok": True, "fbx_output_path": fbx_full_path}\n\n    except Exception as e:\n        result = {"ok": False, "error": str(e), "traceback": traceback.format_exc()}\n\n    with result_path.open("wb") as f:\n        pickle.dump(result, f)\n\n\nif __name__ == "__main__":\n    _main()\n\'\'\'\n\n\ndef _find_comfy_root(start: Path) -> Path:\n    current = start.resolve()\n    for parent in [current] + list(current.parents):\n        if (parent / "main.py").exists() and (parent / "folder_paths.py").exists():\n            return parent\n    return start.resolve()\n\n\ndef _find_env_python(nodes_dir: Path) -> Path:\n    env_dirs = sorted(\n        [p for p in nodes_dir.iterdir() if p.name.startswith("_env_")],\n        key=lambda p: p.stat().st_mtime if p.exists() else 0,\n        reverse=True,\n    )\n    checked = []\n    for env_dir in env_dirs:\n        candidates = [\n            env_dir / "python.exe",\n            env_dir / ".pixi" / "envs" / "default" / "python.exe",\n            env_dir / "bin" / "python",\n            env_dir / ".pixi" / "envs" / "default" / "bin" / "python",\n        ]\n        for c in candidates:\n            checked.append(str(c))\n            if c.exists():\n                return c\n    raise RuntimeError("UniRig isolated env Python not found. Checked:\\n" + "\\n".join(checked))\n\n\ndef _is_junction_or_symlink(path: Path) -> bool:\n    try:\n        if path.is_symlink():\n            return True\n        if os.name == "nt":\n            import stat\n            attrs = os.stat(path, follow_symlinks=False).st_file_attributes\n            return bool(attrs & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))\n    except Exception:\n        return False\n    return False\n\n\nclass UniRigAutoRig:\n    """Single node for complete rigging pipeline, executed in isolated UniRig env."""\n\n    @classmethod\n    def INPUT_TYPES(cls):\n        return {\n            "required": {\n                "trimesh": ("TRIMESH",),\n                "model": ("UNIRIG_MODEL", {"tooltip": "Pre-loaded UniRig model (from UniRigLoadModel)"}),\n            },\n            "optional": {\n                "skeleton_template": (["mixamo", "articulationxl"], {\n                    "default": "mixamo",\n                    "tooltip": "Skeleton template. \'mixamo\' remaps to Mixamo bone names (humanoids). \'articulationxl\' outputs native skeleton (any 3D asset)."\n                }),\n                "fbx_name": ("STRING", {\n                    "default": "",\n                    "tooltip": "Custom filename for saved FBX (without extension). If empty, uses auto-generated name."\n                }),\n                "target_face_count": ("INT", {\n                    "default": 50000,\n                    "min": 10000,\n                    "max": 500000,\n                    "step": 10000,\n                    "tooltip": "Target face count for mesh decimation. Warning: changing from default may reduce quality."\n                }),\n            }\n        }\n\n    RETURN_TYPES = ("STRING",)\n    RETURN_NAMES = ("fbx_output_path",)\n    FUNCTION = "auto_rig"\n    CATEGORY = "UniRig"\n\n    def auto_rig(self, trimesh, model, skeleton_template="mixamo", fbx_name="", target_face_count=50000):\n        total_start = time.time()\n        log.info("Starting complete rigging pipeline via UniRig isolated env runner...")\n        log.info("Skeleton template: %s", skeleton_template)\n\n        this_file = Path(__file__).resolve()\n        nodes_dir = this_file.parent\n        custom_node_root = nodes_dir.parent\n\n        try:\n            import folder_paths as _fp_for_root\n            comfy_root = Path(_fp_for_root.__file__).resolve().parent\n        except Exception:\n            comfy_root = _find_comfy_root(custom_node_root)\n\n        env_python = _find_env_python(nodes_dir)\n        log.info("ComfyUI root for env runner: %s", comfy_root)\n        log.info("UniRig custom node root: %s", custom_node_root)\n        log.info("UniRig nodes dir: %s", nodes_dir)\n        log.info("UniRig env python: %s", env_python)\n\n        for p in nodes_dir.iterdir():\n            if p.name.startswith("_env_"):\n                log.info("UniRig env link candidate: %s (junction/symlink=%s)", p, _is_junction_or_symlink(p))\n\n        try:\n            import folder_paths\n            temp_base = Path(folder_paths.get_temp_directory())\n            output_dir = Path(folder_paths.get_output_directory())\n        except Exception:\n            temp_base = Path(tempfile.gettempdir())\n            output_dir = Path.cwd()\n\n        temp_base.mkdir(parents=True, exist_ok=True)\n        output_dir.mkdir(parents=True, exist_ok=True)\n\n        with tempfile.TemporaryDirectory(prefix="unirig_env_runner_", dir=str(temp_base), ignore_cleanup_errors=True) as tmp:\n            tmpdir = Path(tmp)\n            worker_path = tmpdir / "unirig_env_worker.py"\n            payload_path = tmpdir / "payload.pkl"\n            result_path = tmpdir / "result.pkl"\n            worker_path.write_text(_WORKER_CODE, encoding="utf-8")\n\n            payload = {\n                "trimesh": trimesh,\n                "model": model,\n                "skeleton_template": skeleton_template,\n                "fbx_name": fbx_name,\n                "target_face_count": target_face_count,\n                "comfy_root": str(comfy_root),\n                "custom_node_root": str(custom_node_root),\n                "nodes_dir": str(nodes_dir),\n                "temp_dir": str(temp_base),\n                "output_dir": str(output_dir),\n            }\n            with payload_path.open("wb") as f:\n                pickle.dump(payload, f)\n\n            env = os.environ.copy()\n            env["PYTHONIOENCODING"] = "utf-8"\n            env["PYTHONUTF8"] = "1"\n            pythonpath_entries = [str(comfy_root), str(custom_node_root), str(nodes_dir)]\n            existing_pp = env.get("PYTHONPATH")\n            if existing_pp:\n                pythonpath_entries.append(existing_pp)\n            env["PYTHONPATH"] = os.pathsep.join(pythonpath_entries)\n            env["UNIRIG_ENV_RUNNER"] = "1"\n\n            cmd = [str(env_python), str(worker_path), str(payload_path), str(result_path)]\n            log.info("Launching UniRig env runner subprocess...")\n            log.info("$ %s", " ".join((\'"%s"\' % x) if " " in x else x for x in cmd))\n\n            proc = subprocess.run(\n                cmd,\n                cwd=str(custom_node_root),\n                env=env,\n                text=True,\n                encoding="utf-8",\n                errors="replace",\n                stdout=subprocess.PIPE,\n                stderr=subprocess.PIPE,\n            )\n            if proc.stdout:\n                for line in proc.stdout.splitlines():\n                    log.info("[env-runner stdout] %s", line)\n            if proc.stderr:\n                for line in proc.stderr.splitlines():\n                    log.warning("[env-runner stderr] %s", line)\n            if proc.returncode != 0:\n                raise RuntimeError(\n                    f"UniRig env runner failed with exit code {proc.returncode}.\\nSTDERR:\\n{proc.stderr[-4000:]}"\n                )\n            if not result_path.exists():\n                raise RuntimeError("UniRig env runner did not produce a result file.")\n            with result_path.open("rb") as f:\n                result = pickle.load(f)\n            if not result.get("ok"):\n                raise RuntimeError(\n                    "UniRig env runner failed:\\n"\n                    + result.get("error", "unknown error")\n                    + "\\n\\n"\n                    + result.get("traceback", "")\n                )\n            fbx_output_path = result["fbx_output_path"]\n\n        total_time = time.time() - total_start\n        log.info("========================================")\n        log.info("Complete rigging pipeline finished via env runner!")\n        log.info("Total time: %.2fs", total_time)\n        log.info("Output: %s", fbx_output_path)\n        log.info("========================================")\n        return (fbx_output_path,)\n',
    'mesh_io.py': '# UNIRIG_MESH_IO_MANUAL_PATH_V2\n"""\nUniRig Mesh I/O Nodes - Load and save mesh files\n"""\n\nimport os\nimport subprocess\nimport tempfile\nimport numpy as np\nimport trimesh\nimport igl\nfrom pathlib import Path\nfrom typing import Tuple, Optional\n\nimport logging\n\nlog = logging.getLogger("unirig")\n\n\ndef _detect_comfy_user_root():\n    """Return the Desktop ComfyUI user root, even inside comfy-env workers."""\n    # 1) Prefer a path already present in sys.path, injected by comfy-env/Desktop.\n    try:\n        import sys\n        for entry in sys.path:\n            if not entry:\n                continue\n            pp = Path(entry)\n            if (pp / "input").exists() or (pp / "user").exists() or (pp / ".venv").exists():\n                if pp.name.lower() == "comfyui":\n                    return pp\n    except Exception:\n        pass\n\n    # 2) Stable Desktop fallback.\n    candidate = Path.home() / "Documents" / "ComfyUI"\n    if candidate.exists():\n        return candidate\n\n    # 3) Last resort: current working tree.\n    return Path.cwd()\n\n\ndef _get_input_output_folders():\n    """Resolve ComfyUI input/output folders safely in normal ComfyUI and isolated workers."""\n    try:\n        import folder_paths\n        inp = folder_paths.get_input_directory()\n        out = folder_paths.get_output_directory()\n        if inp and out:\n            return inp, out\n    except Exception:\n        pass\n\n    root = _detect_comfy_user_root()\n    inp = root / "input"\n    out = root / "output"\n    out.mkdir(parents=True, exist_ok=True)\n    return str(inp), str(out)\n\n\nCOMFYUI_INPUT_FOLDER, COMFYUI_OUTPUT_FOLDER = _get_input_output_folders()\n\n\ndef _refresh_comfy_folders():\n    global COMFYUI_INPUT_FOLDER, COMFYUI_OUTPUT_FOLDER\n    COMFYUI_INPUT_FOLDER, COMFYUI_OUTPUT_FOLDER = _get_input_output_folders()\n    return COMFYUI_INPUT_FOLDER, COMFYUI_OUTPUT_FOLDER\n\n\n# Import LIB_DIR from base module. Support both package import and comfy-env metadata scan.\ntry:\n    from .base import LIB_DIR\nexcept Exception:\n    import sys\n    _nodes_dir = Path(__file__).resolve().parent\n    if str(_nodes_dir) not in sys.path:\n        sys.path.insert(0, str(_nodes_dir))\n    from base import LIB_DIR\n\ndef load_fbx_with_blender(file_path: str) -> Tuple[Optional[trimesh.Trimesh], str]:\n    """\n    FBX loading is no longer supported via Blender.\n\n    Args:\n        file_path: Path to FBX file\n\n    Returns:\n        Tuple of (None, error_message)\n    """\n    return None, (\n        "FBX file format is not directly supported.\\n\\n"\n        "Please convert your FBX to GLB/OBJ format using Blender or other software,\\n"\n        "then load the converted file."\n    )\n\n\ndef load_mesh_file(file_path: str) -> Tuple[Optional[trimesh.Trimesh], str]:\n    """\n    Load a mesh from file.\n\n    Ensures the returned mesh has only triangular faces and is properly processed.\n\n    Args:\n        file_path: Path to mesh file (OBJ, PLY, STL, OFF, FBX, etc.)\n\n    Returns:\n        Tuple of (mesh, error_message)\n    """\n    if not os.path.exists(file_path):\n        return None, f"File not found: {file_path}"\n\n    # Check file extension - FBX requires Blender (use os.path for Windows compatibility)\n    _, ext = os.path.splitext(file_path)\n    ext = ext.lower()\n    log.info("File extension detected: \'%s\'", ext)\n\n    if ext == \'.fbx\':\n        log.info("Detected FBX file, using Blender loader")\n        return load_fbx_with_blender(file_path)\n\n    try:\n        log.info("Loading: %s", file_path)\n\n        # Try to load with trimesh first (supports many formats)\n        # Do NOT use force=\'mesh\' as it can lose visual/texture data during Scene-to-mesh conversion\n        # Use process=False and maintain_order=True to preserve mesh.visual (textures/materials)\n        loaded = trimesh.load(file_path, process=False, maintain_order=True)\n\n        log.info(f"Loaded type: {type(loaded).__name__}")\n\n        # Debug: Check visual data immediately after load\n        if isinstance(loaded, trimesh.Scene):\n            log.info(f"Scene has {len(loaded.geometry)} geometries")\n            for name, geom in loaded.geometry.items():\n                if hasattr(geom, \'visual\'):\n                    log.info(f"Geometry \'{name}\': visual type = {type(geom.visual).__name__}")\n                    if hasattr(geom.visual, \'material\'):\n                        mat = geom.visual.material\n                        log.info(f"Material: {type(mat).__name__}")\n                        if hasattr(mat, \'baseColorTexture\') and mat.baseColorTexture is not None:\n                            log.info(f"Has baseColorTexture: {mat.baseColorTexture.shape if hasattr(mat.baseColorTexture, \'shape\') else \'yes\'}")\n                        if hasattr(mat, \'image\') and mat.image is not None:\n                            log.info(f"Has image: {mat.image.size if hasattr(mat.image, \'size\') else \'yes\'}")\n        else:\n            if hasattr(loaded, \'visual\'):\n                log.info(f"Mesh visual type: {type(loaded.visual).__name__}")\n                if hasattr(loaded.visual, \'material\'):\n                    mat = loaded.visual.material\n                    log.info(f"Material: {type(mat).__name__}")\n\n        # Handle case where trimesh.load returns a Scene instead of a mesh\n        if isinstance(loaded, trimesh.Scene):\n            log.info(f"Converting Scene to single mesh (scene has {len(loaded.geometry)} geometries)")\n            # Use dump with concatenate=True to merge geometries while preserving visual data\n            mesh = loaded.dump(concatenate=True)\n            log.info(f"After dump(): visual type = {type(mesh.visual).__name__ if hasattr(mesh, \'visual\') else \'None\'}")\n            if hasattr(mesh, \'visual\') and hasattr(mesh.visual, \'material\'):\n                log.info(f"After dump(): material = {type(mesh.visual.material).__name__}")\n        else:\n            mesh = loaded\n\n        if mesh is None or len(mesh.vertices) == 0 or len(mesh.faces) == 0:\n            return None, f"Failed to read mesh or mesh is empty: {file_path}"\n\n        log.info(f"Initial mesh: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")\n\n        # Debug: Check visual after initial processing\n        if hasattr(mesh, \'visual\'):\n            log.info(f"Visual type: {type(mesh.visual).__name__}")\n            if hasattr(mesh.visual, \'uv\') and mesh.visual.uv is not None:\n                log.info("Has UV coords: %s", mesh.visual.uv.shape)\n            if hasattr(mesh.visual, \'material\') and mesh.visual.material is not None:\n                mat = mesh.visual.material\n                log.info(f"Material type: {type(mat).__name__}")\n                if hasattr(mat, \'baseColorTexture\') and mat.baseColorTexture is not None:\n                    log.info("Has baseColorTexture!")\n                if hasattr(mat, \'image\') and mat.image is not None:\n                    log.info("Has image texture!")\n        else:\n            log.warning("WARNING: No visual attribute on mesh!")\n\n        # Ensure mesh is properly triangulated\n        if hasattr(mesh, \'faces\') and len(mesh.faces) > 0:\n            # Check if faces are triangular\n            if mesh.faces.shape[1] != 3:\n                log.warning("Warning: Mesh has non-triangular faces, triangulating...")\n                # Use process=False to preserve mesh.visual (textures/materials)\n                mesh = trimesh.Trimesh(vertices=mesh.vertices, faces=mesh.faces, process=False, maintain_order=True)\n                log.info(f"After triangulation: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")\n\n        # Count before cleanup\n        verts_before = len(mesh.vertices)\n        faces_before = len(mesh.faces)\n\n        # NOTE: We do NOT call mesh.merge_vertices() here as it destroys mesh.visual (textures/materials)\n\n        # Remove duplicate and degenerate faces (trimesh 4.x compatible)\n        # unique_faces() returns boolean mask of non-duplicate faces\n        # nondegenerate_faces() returns boolean mask of non-degenerate faces\n        unique_mask = mesh.unique_faces()\n        nondegenerate_mask = mesh.nondegenerate_faces()\n        valid_faces_mask = unique_mask & nondegenerate_mask\n        if not valid_faces_mask.all():\n            mesh.update_faces(valid_faces_mask)\n\n        verts_after = len(mesh.vertices)\n        faces_after = len(mesh.faces)\n\n        if verts_before != verts_after or faces_before != faces_after:\n            log.info("Cleanup: %s->%s vertices, %s->%s faces", verts_before, verts_after, faces_before, faces_after)\n            log.info("Removed: %s duplicate vertices, %s bad faces", verts_before - verts_after, faces_before - faces_after)\n\n        # Store file metadata\n        mesh.metadata[\'file_path\'] = file_path\n        mesh.metadata[\'file_name\'] = os.path.basename(file_path)\n        mesh.metadata[\'file_format\'] = os.path.splitext(file_path)[1].lower()\n\n        log.info(f"Successfully loaded: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")\n        return mesh, ""\n\n    except Exception as e:\n        log.info(f"Trimesh failed: {str(e)}, trying libigl fallback...")\n        # Fallback to libigl\n        try:\n            v, f = igl.read_triangle_mesh(file_path)\n            if v is None or f is None or len(v) == 0 or len(f) == 0:\n                return None, f"Failed to read mesh: {file_path}"\n\n            log.info(f"libigl loaded: {len(v)} vertices, {len(f)} faces")\n\n            # Use process=False to preserve mesh.visual (textures/materials)\n            mesh = trimesh.Trimesh(vertices=v, faces=f, process=False, maintain_order=True)\n\n            # Count before cleanup\n            verts_before = len(mesh.vertices)\n            faces_before = len(mesh.faces)\n\n            # NOTE: We do NOT call mesh.merge_vertices() here as it destroys mesh.visual (textures/materials)\n\n            # Remove duplicate and degenerate faces (trimesh 4.x compatible)\n            unique_mask = mesh.unique_faces()\n            nondegenerate_mask = mesh.nondegenerate_faces()\n            valid_faces_mask = unique_mask & nondegenerate_mask\n            if not valid_faces_mask.all():\n                mesh.update_faces(valid_faces_mask)\n\n            verts_after = len(mesh.vertices)\n            faces_after = len(mesh.faces)\n\n            if verts_before != verts_after or faces_before != faces_after:\n                log.info("Cleanup: %s->%s vertices, %s->%s faces", verts_before, verts_after, faces_before, faces_after)\n\n            # Store metadata\n            mesh.metadata[\'file_path\'] = file_path\n            mesh.metadata[\'file_name\'] = os.path.basename(file_path)\n            mesh.metadata[\'file_format\'] = os.path.splitext(file_path)[1].lower()\n\n            log.info(f"Successfully loaded via libigl: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")\n            return mesh, ""\n        except Exception as e2:\n            log.info("Both loaders failed!")\n            return None, f"Error loading mesh: {str(e)}; Fallback error: {str(e2)}"\n\n\ndef save_mesh_file(mesh: trimesh.Trimesh, file_path: str) -> Tuple[bool, str]:\n    """\n    Save a mesh to file.\n\n    Args:\n        mesh: Trimesh object\n        file_path: Output file path\n\n    Returns:\n        Tuple of (success, error_message)\n    """\n    if not isinstance(mesh, trimesh.Trimesh):\n        return False, "Input must be a trimesh.Trimesh object"\n\n    if len(mesh.vertices) == 0 or len(mesh.faces) == 0:\n        return False, "Mesh is empty"\n\n    try:\n        # Ensure output directory exists\n        output_dir = os.path.dirname(file_path)\n        if output_dir and not os.path.exists(output_dir):\n            os.makedirs(output_dir, exist_ok=True)\n\n        # Export the mesh\n        mesh.export(file_path)\n\n        return True, ""\n\n    except Exception as e:\n        return False, f"Error saving mesh: {str(e)}"\n\n\nclass UniRigLoadMesh:\n    """\n    Load a mesh from ComfyUI input or output folder (OBJ, PLY, STL, OFF, etc.)\n    Returns trimesh.Trimesh objects for mesh handling.\n    """\n\n    # Supported mesh extensions for file browser\n    SUPPORTED_EXTENSIONS = [\'.obj\', \'.ply\', \'.stl\', \'.off\', \'.gltf\', \'.glb\', \'.fbx\', \'.dae\', \'.3ds\', \'.vtp\']\n\n    @classmethod\n    def INPUT_TYPES(cls):\n        # Manual path input: avoids ComfyUI/comfy-env dropdown desync on Desktop Local.\n        # Examples:\n        #   3d/realistic_male_character.glb\n        #   realistic_male_character.glb\n        #   C:/Users/Frank/Documents/ComfyUI/input/3d/realistic_male_character.glb\n        return {\n            "required": {\n                "source_folder": (["input", "output"], {\n                    "default": "input",\n                    "tooltip": "Base folder used for relative paths: ComfyUI input or output."\n                }),\n                "file_path": ("STRING", {\n                    "default": "3d/realistic_male_character.glb",\n                    "multiline": False,\n                    "tooltip": "Manual mesh path. Relative to input/output, or absolute path. Example: 3d/realistic_male_character.glb"\n                }),\n            },\n        }\n\n    RETURN_TYPES = ("TRIMESH",)\n    RETURN_NAMES = ("mesh",)\n    FUNCTION = "load_mesh"\n    CATEGORY = "UniRig/IO"\n\n    @classmethod\n    def get_mesh_files_from_input(cls):\n        """Get list of available mesh files in input/3d and input folders."""\n        mesh_files = []\n        input_folder, _ = _refresh_comfy_folders()\n\n        if input_folder is not None:\n            # Scan input/3d first\n            input_3d = os.path.join(input_folder, "3d")\n            if os.path.exists(input_3d):\n                for file in os.listdir(input_3d):\n                    if any(file.lower().endswith(ext) for ext in cls.SUPPORTED_EXTENSIONS):\n                        mesh_files.append(f"3d/{file}")\n\n            # Then scan input root\n            for file in os.listdir(input_folder):\n                file_path = os.path.join(input_folder, file)\n                if os.path.isfile(file_path):\n                    if any(file.lower().endswith(ext) for ext in cls.SUPPORTED_EXTENSIONS):\n                        mesh_files.append(file)\n\n        return sorted(mesh_files)\n\n    @classmethod\n    def get_mesh_files_from_output(cls):\n        """Get list of available mesh files in output folder."""\n        mesh_files = []\n        _, output_folder = _refresh_comfy_folders()\n\n        if output_folder is not None and os.path.exists(output_folder):\n            # Scan output folder recursively\n            for root, dirs, files in os.walk(output_folder):\n                for file in files:\n                    if any(file.lower().endswith(ext) for ext in cls.SUPPORTED_EXTENSIONS):\n                        # Get relative path from output folder\n                        full_path = os.path.join(root, file)\n                        rel_path = os.path.relpath(full_path, output_folder)\n                        mesh_files.append(rel_path)\n\n        return sorted(mesh_files)\n\n    @classmethod\n    def IS_CHANGED(cls, source_folder, file_path):\n        """Force re-execution when file changes."""\n        input_folder, output_folder = _refresh_comfy_folders()\n        base_folder = input_folder if source_folder == "input" else output_folder\n\n        if base_folder is not None:\n            if source_folder == "input":\n                # Check in input/3d first, then input root\n                input_3d_path = os.path.join(base_folder, "3d", file_path)\n                input_path = os.path.join(base_folder, file_path)\n\n                if os.path.exists(input_3d_path):\n                    return os.path.getmtime(input_3d_path)\n                elif os.path.exists(input_path):\n                    return os.path.getmtime(input_path)\n            else:\n                # Check in output folder\n                full_path = os.path.join(base_folder, file_path)\n                if os.path.exists(full_path):\n                    return os.path.getmtime(full_path)\n\n        return f"{source_folder}:{file_path}"\n\n    def load_mesh(self, source_folder, file_path):\n        """\n        Load mesh from file.\n\n        Looks for files in the specified source folder (input or output).\n\n        Args:\n            source_folder: "input" or "output"\n            file_path: Path to mesh file (relative to source folder or absolute)\n\n        Returns:\n            tuple: (trimesh.Trimesh,)\n        """\n        if not file_path or file_path.strip() == "":\n            raise ValueError("File path cannot be empty")\n\n        input_folder, output_folder = _refresh_comfy_folders()\n\n        # Try to find the file\n        full_path = None\n        searched_paths = []\n\n        if source_folder == "input" and input_folder is not None:\n            # First, try in ComfyUI input/3d folder\n            input_3d_path = os.path.join(input_folder, "3d", file_path)\n            searched_paths.append(input_3d_path)\n            if os.path.exists(input_3d_path):\n                full_path = input_3d_path\n                log.info("Found mesh in input/3d folder: %s", file_path)\n\n            # Second, try in ComfyUI input folder\n            if full_path is None:\n                input_path = os.path.join(input_folder, file_path)\n                searched_paths.append(input_path)\n                if os.path.exists(input_path):\n                    full_path = input_path\n                    log.info("Found mesh in input folder: %s", file_path)\n\n        elif source_folder == "output" and output_folder is not None:\n            output_path = os.path.join(output_folder, file_path)\n            searched_paths.append(output_path)\n            if os.path.exists(output_path):\n                full_path = output_path\n                log.info("Found mesh in output folder: %s", file_path)\n\n        # If not found in source folder, try as absolute path\n        if full_path is None:\n            searched_paths.append(file_path)\n            if os.path.exists(file_path):\n                full_path = file_path\n                log.info("Loading from absolute path: %s", file_path)\n            else:\n                # Generate error message with all searched paths\n                error_msg = f"File not found: \'{file_path}\'\\nSearched in:"\n                for path in searched_paths:\n                    error_msg += f"\\n  - {path}"\n                raise ValueError(error_msg)\n\n        # Load the mesh\n        loaded_mesh, error = load_mesh_file(full_path)\n\n        if loaded_mesh is None:\n            raise ValueError(f"Failed to load mesh: {error}")\n\n        log.info(f"Loaded: {len(loaded_mesh.vertices)} vertices, {len(loaded_mesh.faces)} faces")\n\n        return (loaded_mesh,)\n\n\nclass UniRigSaveMesh:\n    """\n    Save a mesh to file (OBJ, PLY, STL, OFF, etc.)\n    Supports all formats provided by trimesh.\n    """\n\n    @classmethod\n    def INPUT_TYPES(cls):\n        return {\n            "required": {\n                "trimesh": ("TRIMESH",),\n                "file_path": ("STRING", {\n                    "default": "output.obj",\n                    "multiline": False\n                }),\n            },\n        }\n\n    RETURN_TYPES = ("STRING",)\n    RETURN_NAMES = ("status",)\n    FUNCTION = "save_mesh"\n    CATEGORY = "UniRig/IO"\n    OUTPUT_NODE = True\n\n    def save_mesh(self, trimesh, file_path):\n        """\n        Save mesh to file.\n\n        Saves to ComfyUI\'s output folder if path is relative, otherwise uses absolute path.\n\n        Args:\n            trimesh: trimesh.Trimesh object\n            file_path: Output file path (relative to output folder or absolute)\n\n        Returns:\n            tuple: (status_message,)\n        """\n        if not file_path or file_path.strip() == "":\n            raise ValueError("File path cannot be empty")\n\n        # Debug: Check what we received\n        log.info(f"Received mesh type: {type(trimesh)}")\n        if trimesh is None:\n            raise ValueError("Cannot save mesh: received None instead of a mesh object. Check that the previous node is outputting a mesh.")\n\n        # Check if mesh has data\n        try:\n            vertex_count = len(trimesh.vertices) if hasattr(trimesh, \'vertices\') else 0\n            face_count = len(trimesh.faces) if hasattr(trimesh, \'faces\') else 0\n            log.info("Mesh has %s vertices, %s faces", vertex_count, face_count)\n\n            if vertex_count == 0 or face_count == 0:\n                raise ValueError(\n                    f"Cannot save empty mesh (vertices: {vertex_count}, faces: {face_count}). "\n                    "Check that the previous node is producing valid geometry."\n                )\n        except Exception as e:\n            raise ValueError(f"Error checking mesh properties: {e}. Received object may not be a valid mesh.")\n\n        # Determine full output path\n        full_path = file_path\n        _, output_folder = _refresh_comfy_folders()\n\n        # If path is relative and we have output folder, use it\n        if not os.path.isabs(file_path) and output_folder is not None:\n            full_path = os.path.join(output_folder, file_path)\n            log.info("Saving to output folder: %s", file_path)\n        else:\n            log.info("Saving to: %s", file_path)\n\n        # Save the mesh\n        success, error = save_mesh_file(trimesh, full_path)\n\n        if not success:\n            raise ValueError(f"Failed to save trimesh: {error}")\n\n        status = f"Successfully saved mesh to: {full_path}\\n"\n        status += f"  Vertices: {len(trimesh.vertices)}\\n"\n        status += f"  Faces: {len(trimesh.faces)}"\n\n        log.info("%s", status)\n\n        return (status,)\n',
    'base.py': '# UNIRIG_BASE_FOLDER_PATHS_SAFE_V1\n"""\nBase setup and shared utilities for UniRig nodes.\n\nHandles path configuration, Blender setup, and HuggingFace cache management.\n"""\n\nimport logging\nimport os\nfrom pathlib import Path\nimport numpy as np\nimport base64\nfrom io import BytesIO\n\ntry:\n    import folder_paths\nexcept Exception:\n    folder_paths = None\n\nlog = logging.getLogger("unirig")\n\n# Try to import PIL for texture handling\ntry:\n    from PIL import Image as PILImage\n    HAS_PIL = True\nexcept ImportError:\n    HAS_PIL = False\n    log.warning("PIL not available, texture preview will be limited")\n\n\n# Get paths relative to this file\nNODE_DIR = Path(__file__).parent.parent.absolute()  # Go up from nodes/ to ComfyUI-UniRig/\nNODES_DIR = Path(__file__).parent.absolute()  # nodes/ directory itself\nUNIRIG_PATH = str(NODES_DIR / "unirig")\n# Keep LIB_DIR for backwards compatibility\nLIB_DIR = NODES_DIR\n\n# Set up UniRig models directory.\n# In normal ComfyUI runtime, use ComfyUI\'s models folder.\n# During comfy-env metadata scan, folder_paths is not available, so use a safe\n# local fallback only to let node registration complete.\nif folder_paths is not None:\n    UNIRIG_MODELS_DIR = Path(folder_paths.models_dir) / "unirig"\nelse:\n    UNIRIG_MODELS_DIR = NODE_DIR / "models" / "unirig"\n\ntry:\n    UNIRIG_MODELS_DIR.mkdir(parents=True, exist_ok=True)\nexcept Exception:\n    pass\n\nos.environ[\'UNIRIG_MODELS_DIR\'] = str(UNIRIG_MODELS_DIR)\n\nlog.info("Models directory: %s", UNIRIG_MODELS_DIR)\n\nimport shutil\n\n\ndef decode_texture_to_comfy_image(texture_data_base64: str):\n    """\n    Decode base64 texture to ComfyUI IMAGE format (torch tensor).\n\n    Args:\n        texture_data_base64: Base64-encoded image data\n\n    Returns:\n        tuple: (torch tensor [1, H, W, 3], width, height) or (None, 0, 0)\n    """\n    if not texture_data_base64 or not HAS_PIL:\n        return None, 0, 0\n\n    try:\n        import torch  # Lazy import\n\n        # Decode base64\n        image_data = base64.b64decode(texture_data_base64)\n        pil_image = PILImage.open(BytesIO(image_data))\n\n        # Convert to RGB if necessary\n        if pil_image.mode == \'RGBA\':\n            pil_image = pil_image.convert(\'RGB\')\n        elif pil_image.mode != \'RGB\':\n            pil_image = pil_image.convert(\'RGB\')\n\n        # Convert to numpy array\n        img_array = np.array(pil_image).astype(np.float32) / 255.0\n\n        # Convert to torch tensor [1, H, W, 3] for ComfyUI\n        img_tensor = torch.from_numpy(img_array).unsqueeze(0)\n\n        return img_tensor, pil_image.width, pil_image.height\n\n    except Exception as e:\n        log.error("Error decoding texture: %s", e)\n        return None, 0, 0\n\n\ndef create_placeholder_texture(width: int = 256, height: int = 256, text: str = "No Texture"):\n    """\n    Create a placeholder image when no texture is available.\n\n    Args:\n        width: Image width\n        height: Image height\n        text: Text to display (not currently rendered, just for reference)\n\n    Returns:\n        torch.Tensor: Placeholder image tensor [1, H, W, 3]\n    """\n    import torch  # Lazy import\n\n    try:\n        # Create a gray image with text\n        img_array = np.full((height, width, 3), 0.3, dtype=np.float32)\n\n        # Add a simple pattern to indicate placeholder\n        # Create a grid pattern\n        for i in range(0, height, 32):\n            img_array[i:i+2, :, :] = 0.4\n        for j in range(0, width, 32):\n            img_array[:, j:j+2, :] = 0.4\n\n        img_tensor = torch.from_numpy(img_array).unsqueeze(0)\n        return img_tensor\n\n    except Exception as e:\n        log.error("Error creating placeholder: %s", e)\n        # Return minimal gray image\n        return torch.full((1, 64, 64, 3), 0.3)\n',
    'skeleton_extraction.py': '"""\nSkeleton extraction nodes for UniRig.\n\nUses comfy-env isolated environment for GPU dependencies.\nUses direct Python inference with bpy for mesh preprocessing.\n"""\n\nimport os\nimport sys\nimport tempfile\nimport numpy as np\nfrom trimesh import Trimesh\nimport time\ntry:\n    import folder_paths\nexcept Exception:\n    folder_paths = None\n\ndef _unirig_temp_directory():\n    if folder_paths is not None:\n        return folder_paths.get_temp_directory()\n    import tempfile\n    return tempfile.gettempdir()\n\nimport logging\n\nlog = logging.getLogger("unirig")\n# UNIRIG_FOLDER_PATHS_SAFE_SKELETON_V1\nTARGET_FACE_COUNT = 50000  # default for mesh decimation\n\ntry:\n    from .base import (\n        UNIRIG_PATH,\n        UNIRIG_MODELS_DIR,\n        decode_texture_to_comfy_image,\n        create_placeholder_texture,\n    )\nexcept ImportError:\n    from base import (\n        UNIRIG_PATH,\n        UNIRIG_MODELS_DIR,\n        decode_texture_to_comfy_image,\n        create_placeholder_texture,\n    )\n\n# VRoid to Mixamo bone name mapping (52 bones, 1:1 correspondence)\nVROID_TO_MIXAMO_BONE_MAP = {\n    # Body (22 bones)\n    "J_Bip_C_Hips": "mixamorig:Hips",\n    "J_Bip_C_Spine": "mixamorig:Spine",\n    "J_Bip_C_Chest": "mixamorig:Spine1",\n    "J_Bip_C_UpperChest": "mixamorig:Spine2",\n    "J_Bip_C_Neck": "mixamorig:Neck",\n    "J_Bip_C_Head": "mixamorig:Head",\n    "J_Bip_L_Shoulder": "mixamorig:LeftShoulder",\n    "J_Bip_L_UpperArm": "mixamorig:LeftArm",\n    "J_Bip_L_LowerArm": "mixamorig:LeftForeArm",\n    "J_Bip_L_Hand": "mixamorig:LeftHand",\n    "J_Bip_R_Shoulder": "mixamorig:RightShoulder",\n    "J_Bip_R_UpperArm": "mixamorig:RightArm",\n    "J_Bip_R_LowerArm": "mixamorig:RightForeArm",\n    "J_Bip_R_Hand": "mixamorig:RightHand",\n    "J_Bip_L_UpperLeg": "mixamorig:LeftUpLeg",\n    "J_Bip_L_LowerLeg": "mixamorig:LeftLeg",\n    "J_Bip_L_Foot": "mixamorig:LeftFoot",\n    "J_Bip_L_ToeBase": "mixamorig:LeftToeBase",\n    "J_Bip_R_UpperLeg": "mixamorig:RightUpLeg",\n    "J_Bip_R_LowerLeg": "mixamorig:RightLeg",\n    "J_Bip_R_Foot": "mixamorig:RightFoot",\n    "J_Bip_R_ToeBase": "mixamorig:RightToeBase",\n    # Left Hand (15 bones)\n    "J_Bip_L_Thumb1": "mixamorig:LeftHandThumb1",\n    "J_Bip_L_Thumb2": "mixamorig:LeftHandThumb2",\n    "J_Bip_L_Thumb3": "mixamorig:LeftHandThumb3",\n    "J_Bip_L_Index1": "mixamorig:LeftHandIndex1",\n    "J_Bip_L_Index2": "mixamorig:LeftHandIndex2",\n    "J_Bip_L_Index3": "mixamorig:LeftHandIndex3",\n    "J_Bip_L_Middle1": "mixamorig:LeftHandMiddle1",\n    "J_Bip_L_Middle2": "mixamorig:LeftHandMiddle2",\n    "J_Bip_L_Middle3": "mixamorig:LeftHandMiddle3",\n    "J_Bip_L_Ring1": "mixamorig:LeftHandRing1",\n    "J_Bip_L_Ring2": "mixamorig:LeftHandRing2",\n    "J_Bip_L_Ring3": "mixamorig:LeftHandRing3",\n    "J_Bip_L_Little1": "mixamorig:LeftHandPinky1",\n    "J_Bip_L_Little2": "mixamorig:LeftHandPinky2",\n    "J_Bip_L_Little3": "mixamorig:LeftHandPinky3",\n    # Right Hand (15 bones)\n    "J_Bip_R_Thumb1": "mixamorig:RightHandThumb1",\n    "J_Bip_R_Thumb2": "mixamorig:RightHandThumb2",\n    "J_Bip_R_Thumb3": "mixamorig:RightHandThumb3",\n    "J_Bip_R_Index1": "mixamorig:RightHandIndex1",\n    "J_Bip_R_Index2": "mixamorig:RightHandIndex2",\n    "J_Bip_R_Index3": "mixamorig:RightHandIndex3",\n    "J_Bip_R_Middle1": "mixamorig:RightHandMiddle1",\n    "J_Bip_R_Middle2": "mixamorig:RightHandMiddle2",\n    "J_Bip_R_Middle3": "mixamorig:RightHandMiddle3",\n    "J_Bip_R_Ring1": "mixamorig:RightHandRing1",\n    "J_Bip_R_Ring2": "mixamorig:RightHandRing2",\n    "J_Bip_R_Ring3": "mixamorig:RightHandRing3",\n    "J_Bip_R_Little1": "mixamorig:RightHandPinky1",\n    "J_Bip_R_Little2": "mixamorig:RightHandPinky2",\n    "J_Bip_R_Little3": "mixamorig:RightHandPinky3",\n}\n\n# VRoid to SMPL bone mapping (22 joints - maps VRoid bones to SMPL joint names)\nVROID_TO_SMPL_BONE_MAP = {\n    "J_Bip_C_Hips": "Pelvis",           # 0\n    "J_Bip_L_UpperLeg": "L_Hip",         # 1\n    "J_Bip_R_UpperLeg": "R_Hip",         # 2\n    "J_Bip_C_Spine": "Spine1",           # 3\n    "J_Bip_L_LowerLeg": "L_Knee",        # 4\n    "J_Bip_R_LowerLeg": "R_Knee",        # 5\n    "J_Bip_C_Chest": "Spine2",           # 6\n    "J_Bip_L_Foot": "L_Ankle",           # 7\n    "J_Bip_R_Foot": "R_Ankle",           # 8\n    "J_Bip_C_UpperChest": "Spine3",      # 9\n    "J_Bip_L_ToeBase": "L_Foot",         # 10\n    "J_Bip_R_ToeBase": "R_Foot",         # 11\n    "J_Bip_C_Neck": "Neck",              # 12\n    "J_Bip_L_Shoulder": "L_Collar",      # 13\n    "J_Bip_R_Shoulder": "R_Collar",      # 14\n    "J_Bip_C_Head": "Head",              # 15\n    "J_Bip_L_UpperArm": "L_Shoulder",    # 16\n    "J_Bip_R_UpperArm": "R_Shoulder",    # 17\n    "J_Bip_L_LowerArm": "L_Elbow",       # 18\n    "J_Bip_R_LowerArm": "R_Elbow",       # 19\n    "J_Bip_L_Hand": "L_Wrist",           # 20\n    "J_Bip_R_Hand": "R_Wrist",           # 21\n}\n\n# SMPL joint names in order (22 joints)\nSMPL_JOINT_NAMES = [\n    \'Pelvis\', \'L_Hip\', \'R_Hip\', \'Spine1\', \'L_Knee\', \'R_Knee\',\n    \'Spine2\', \'L_Ankle\', \'R_Ankle\', \'Spine3\', \'L_Foot\', \'R_Foot\',\n    \'Neck\', \'L_Collar\', \'R_Collar\', \'Head\', \'L_Shoulder\', \'R_Shoulder\',\n    \'L_Elbow\', \'R_Elbow\', \'L_Wrist\', \'R_Wrist\'\n]\n\n# SMPL parent hierarchy (22 joints) - index of parent for each joint\nSMPL_PARENTS = [\n    -1,  # 0: Pelvis (root)\n    0,   # 1: L_Hip -> Pelvis\n    0,   # 2: R_Hip -> Pelvis\n    0,   # 3: Spine1 -> Pelvis\n    1,   # 4: L_Knee -> L_Hip\n    2,   # 5: R_Knee -> R_Hip\n    3,   # 6: Spine2 -> Spine1\n    4,   # 7: L_Ankle -> L_Knee\n    5,   # 8: R_Ankle -> R_Knee\n    6,   # 9: Spine3 -> Spine2\n    7,   # 10: L_Foot -> L_Ankle\n    8,   # 11: R_Foot -> R_Ankle\n    9,   # 12: Neck -> Spine3\n    9,   # 13: L_Collar -> Spine3\n    9,   # 14: R_Collar -> Spine3\n    12,  # 15: Head -> Neck\n    13,  # 16: L_Shoulder -> L_Collar\n    14,  # 17: R_Shoulder -> R_Collar\n    16,  # 18: L_Elbow -> L_Shoulder\n    17,  # 19: R_Elbow -> R_Shoulder\n    18,  # 20: L_Wrist -> L_Elbow\n    19,  # 21: R_Wrist -> R_Elbow\n]\n\n# SMPL canonical bone directions (unit vectors pointing from head to tail)\n# These define how each bone should be oriented in rest pose\n# Coordinate system: Blender default (X=right, Y=forward, Z=up)\n# These get rotated to SMPL coords (Y-up) when skeleton_template="smpl"\n# For symmetric bones, L and R have mirrored X component (left/right)\nSMPL_BONE_DIRECTIONS = {\n    \'Pelvis\':     [0, 0, 1],      # Up +Z (toward spine)\n    \'L_Hip\':      [0, 0, -1],     # Down -Z (toward knee)\n    \'R_Hip\':      [0, 0, -1],     # Down -Z (toward knee)\n    \'Spine1\':     [0, 0, 1],      # Up +Z\n    \'L_Knee\':     [0, 0, -1],     # Down -Z (toward ankle)\n    \'R_Knee\':     [0, 0, -1],     # Down -Z (toward ankle)\n    \'Spine2\':     [0, 0, 1],      # Up +Z\n    \'L_Ankle\':    [0, 1, 0],      # Forward +Y (toward toe)\n    \'R_Ankle\':    [0, 1, 0],      # Forward +Y (toward toe)\n    \'Spine3\':     [0, 0, 1],      # Up +Z\n    \'L_Foot\':     [0, 1, 0],      # Forward +Y\n    \'R_Foot\':     [0, 1, 0],      # Forward +Y\n    \'Neck\':       [0, 0, 1],      # Up +Z\n    \'L_Collar\':   [1, 0, 0],      # Left +X (toward shoulder)\n    \'R_Collar\':   [-1, 0, 0],     # Right -X (toward shoulder)\n    \'Head\':       [0, 0, 1],      # Up +Z\n    \'L_Shoulder\': [1, 0, 0],      # Left +X (toward elbow)\n    \'R_Shoulder\': [-1, 0, 0],     # Right -X (toward elbow)\n    \'L_Elbow\':    [1, 0, 0],      # Left +X (toward wrist)\n    \'R_Elbow\':    [-1, 0, 0],     # Right -X (toward wrist)\n    \'L_Wrist\':    [1, 0, 0],      # Left +X (toward hand)\n    \'R_Wrist\':    [-1, 0, 0],     # Right -X (toward hand)\n}\n\n# Default bone length for SMPL (used when computing tails)\nSMPL_DEFAULT_BONE_LENGTH = 0.1\n\n# Direct inference module\ntry:\n    from .unirig import direct as _direct_inference_module\nexcept Exception as e:\n    log.info("Direct inference not available: %s", e)\n    _direct_inference_module = None\n\n# Direct preprocessing module (bpy as Python module)\ntry:\n    from .unirig import direct_preprocess as _direct_preprocess_module\nexcept Exception as e:\n    log.info("Direct preprocessing not available: %s", e)\n    _direct_preprocess_module = None\n\n\ndef _get_direct_inference():\n    """Get the direct inference module for in-process model inference."""\n    return _direct_inference_module\n\n\ndef _get_direct_preprocess():\n    """Get the direct preprocessing module for in-process mesh preprocessing using bpy."""\n    return _direct_preprocess_module\n\n\n\nclass UniRigExtractSkeletonNew:\n    """\n    Extract skeleton from mesh using UniRig (SIGGRAPH 2025).\n\n    Uses ML-based approach for high-quality semantic skeleton extraction.\n    Works on any mesh type: humans, animals, objects, cameras, etc.\n\n    Runs in isolated environment with GPU dependencies.\n    Requires pre-loaded model from UniRigLoadSkeletonModel.\n    """\n\n    @classmethod\n    def INPUT_TYPES(cls):\n        return {\n            "required": {\n                "trimesh": ("TRIMESH",),\n                "skeleton_model": ("UNIRIG_SKELETON_MODEL", {\n                    "tooltip": "Pre-loaded skeleton model (from UniRigLoadSkeletonModel) - REQUIRED"\n                }),\n                "seed": ("INT", {"default": 42, "min": 0, "max": 4294967295,\n                               "tooltip": "Random seed for skeleton generation variation"}),\n            },\n            "optional": {\n                "skeleton_template": (["vroid", "mixamo", "smpl", "articulationxl"], {\n                    "default": "mixamo",\n                    "tooltip": "Skeleton template: vroid (52 bones), mixamo (Mixamo-compatible 52 bones), smpl (22 joints, SMPL-compatible for direct motion application), articulationxl (generic/flexible)"\n                }),\n                "target_face_count": ("INT", {\n                    "default": 50000,\n                    "min": 10000,\n                    "max": 500000,\n                    "step": 10000,\n                    "tooltip": "Target face count for mesh decimation. Higher = preserve more detail, slower. Default: 50000"\n                }),\n            }\n        }\n\n    RETURN_TYPES = ("TRIMESH", "SKELETON", "IMAGE")\n    RETURN_NAMES = ("normalized_mesh", "skeleton", "texture_preview")\n    FUNCTION = "extract"\n    CATEGORY = "UniRig"\n\n    def extract(self, trimesh, skeleton_model, seed, skeleton_template="mixamo", target_face_count=None):\n        """Extract skeleton using UniRig with cached model only."""\n        total_start = time.time()\n        log.info("Starting skeleton extraction (cached model only)...")\n        log.info("Skeleton template: %s", skeleton_template)\n\n        # Store original template choice before any remapping\n        original_template = skeleton_template\n\n        # Track if we need to remap to mixamo or smpl naming\n        remap_to_mixamo = (skeleton_template == "mixamo")\n        remap_to_smpl = (skeleton_template == "smpl")\n\n        # If mixamo is requested, use vroid for extraction (model trained on vroid), then remap names\n        if skeleton_template == "mixamo":\n            skeleton_template = "vroid"\n            log.info("Mixamo requested, using vroid extraction + name remapping")\n\n        # If smpl is requested, use vroid for extraction, then filter to 22 SMPL joints\n        if skeleton_template == "smpl":\n            skeleton_template = "vroid"\n            log.info("SMPL requested, using vroid extraction + SMPL conversion")\n\n        # Validate model is provided\n        if skeleton_model is None:\n            raise RuntimeError(\n                "skeleton_model is required for UniRigExtractSkeletonNew. "\n                "Please connect a UniRigLoadSkeletonModel node."\n            )\n\n        # Validate model has checkpoint path\n        if not skeleton_model.get("checkpoint_path"):\n            raise RuntimeError(\n                "skeleton_model checkpoint not found. "\n                "Please connect a UniRigLoadSkeletonModel node."\n            )\n\n        log.info("Using pre-loaded cached model")\n\n        # Check if UniRig is available\n        if not os.path.exists(UNIRIG_PATH):\n            raise RuntimeError(\n                f"UniRig code not found at {UNIRIG_PATH}. "\n                "The lib/unirig directory should contain the UniRig source code."\n            )\n\n        # Create temp files\n        # ignore_cleanup_errors=True prevents Windows errors when npz files are still locked\n        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:\n            input_path = os.path.join(tmpdir, "input.glb")\n            npz_dir = os.path.join(tmpdir, "input")\n            npz_path = os.path.join(npz_dir, "raw_data.npz")\n\n            os.makedirs(npz_dir, exist_ok=True)\n\n            # Export mesh to GLB\n            step_start = time.time()\n            log.info("Exporting mesh to %s", input_path)\n            log.info(f"Mesh has {len(trimesh.vertices)} vertices, {len(trimesh.faces)} faces")\n            trimesh.export(input_path)\n            export_time = time.time() - step_start\n            log.info("Mesh exported in %.2fs", export_time)\n\n            # Step 1: Preprocess mesh using direct bpy import\n            step_start = time.time()\n            actual_face_count = target_face_count if target_face_count is not None else TARGET_FACE_COUNT\n            log.info("Using target face count: %s", actual_face_count)\n\n            direct_preprocess = _get_direct_preprocess()\n            if direct_preprocess is None:\n                raise RuntimeError(\n                    "Direct preprocessing module not available. "\n                    "Ensure bpy is installed: pip install bpy"\n                )\n\n            log.info("Step 1: Preprocessing mesh with direct bpy...")\n            direct_preprocess.preprocess_mesh(\n                input_file=input_path,\n                output_npz=npz_path,\n                target_face_count=actual_face_count\n            )\n\n            if not os.path.exists(npz_path):\n                raise RuntimeError(f"Preprocessing failed: {npz_path} not created")\n\n            preprocess_time = time.time() - step_start\n            log.info("[OK] Mesh preprocessed in %.2fs: %s", preprocess_time, npz_path)\n\n            # Step 2: Run skeleton inference\n            step_start = time.time()\n\n            # Map skeleton template to cls token\n            cls_value = None  # auto (let model decide)\n            if skeleton_template == "vroid" or skeleton_template == "mixamo":\n                cls_value = "vroid"  # Both need VRoid 52-bone skeleton with fingers\n            elif skeleton_template == "articulationxl":\n                cls_value = "articulationxl"\n\n            if cls_value:\n                log.info("Forcing skeleton template: %s", cls_value)\n            else:\n                log.info("Using auto skeleton detection")\n\n            # Run direct inference\n            direct_module = _get_direct_inference()\n            if direct_module is None:\n                raise RuntimeError(\n                    "Direct inference module not available. "\n                    "Ensure all UniRig dependencies are installed."\n                )\n\n            log.info("Step 2: Running skeleton inference...")\n\n            # Load raw_data.npz created by preprocessing\n            raw_data = np.load(npz_path)\n            mesh_vertices_raw = raw_data[\'vertices\']\n            mesh_faces_raw = raw_data[\'faces\']\n            raw_data.close()\n\n            # Get checkpoint path from skeleton_model\n            checkpoint_path = skeleton_model.get("checkpoint_path")\n            if not checkpoint_path:\n                checkpoint_path = os.path.join(UNIRIG_MODELS_DIR, "skeleton.safetensors")\n\n            if not os.path.exists(checkpoint_path):\n                raise RuntimeError(f"Skeleton checkpoint not found: {checkpoint_path}")\n\n            log.info("Using checkpoint: %s", checkpoint_path)\n\n            # Extract dtype and attn_backend from model config (set by UniRigLoadModel)\n            model_dtype = skeleton_model.get("dtype")\n            model_attn_backend = skeleton_model.get("attn_backend", "auto")\n\n            # Run direct skeleton prediction\n            direct_skeleton_result, norm_params = direct_module.predict_skeleton_from_mesh(\n                vertices=mesh_vertices_raw,\n                faces=mesh_faces_raw,\n                skeleton_checkpoint=checkpoint_path,\n                num_samples=2048,\n                cls=cls_value or "articulationxl",\n                max_new_tokens=2048,\n                seed=seed,\n                dtype=model_dtype,\n                attn_backend=model_attn_backend,\n            )\n\n            inference_time = time.time() - step_start\n\n            if direct_skeleton_result[\'joints\'] is None:\n                raise RuntimeError("Skeleton prediction failed - no joints generated")\n\n            num_joints = len(direct_skeleton_result[\'joints\'])\n            log.info("[OK] Inference completed in %.2fs", inference_time)\n            log.info("Generated %s joints", num_joints)\n\n            # Step 3: Process results\n            step_start = time.time()\n            log.info("Step 3: Processing inference results...")\n\n            # Extract skeleton data directly from model output\n            all_joints = direct_skeleton_result[\'joints\']\n            skeleton_bone_parents = direct_skeleton_result[\'parents\']\n            skeleton_bone_names = direct_skeleton_result.get(\'names\')\n            skeleton_bone_to_head = None  # Not needed - joints are already bone heads\n\n            # Create edges from parent relationships\n            edges = []\n            for i, parent in enumerate(skeleton_bone_parents):\n                if parent is not None and parent >= 0:\n                    edges.append([parent, i])\n\n            log.info(f"Results: {len(all_joints)} joints, {len(edges)} edges")\n\n            # Load preprocessing data\n            # For mesh/texture: always use raw_data.npz (has texture data)\n            # For skeleton: use parsed FBX output (has correct bone names from model)\n            preprocessing_npz = os.path.join(tmpdir, "input", "raw_data.npz")\n\n            uv_coords = None\n            uv_faces = None\n            material_name = None\n            texture_path = None\n            texture_data_base64 = None\n            texture_format = None\n            texture_width = 0\n            texture_height = 0\n\n            # Load mesh and texture data from preprocessing NPZ (raw_data.npz)\n            if os.path.exists(preprocessing_npz):\n                log.info("Loading mesh/texture from: raw_data.npz")\n                preprocess_data = np.load(preprocessing_npz, allow_pickle=True)\n\n                # Helper to safely get array field (handles 0-d arrays from None values)\n                def safe_get_array(key):\n                    if key not in preprocess_data:\n                        return None\n                    val = preprocess_data[key]\n                    if hasattr(val, \'ndim\') and val.ndim == 0:\n                        # 0-d array (scalar) - treat as None\n                        return None\n                    return val\n\n                mesh_vertices_original = preprocess_data[\'vertices\']\n                mesh_faces = preprocess_data[\'faces\']\n                vertex_normals = safe_get_array(\'vertex_normals\')\n                face_normals = safe_get_array(\'face_normals\')\n\n                # Load UV coordinates if available\n                uv_coords_data = safe_get_array(\'uv_coords\')\n                if uv_coords_data is not None and len(uv_coords_data) > 0:\n                    uv_coords = uv_coords_data\n                    uv_faces = safe_get_array(\'uv_faces\')\n                    log.info(f"Loaded UV coordinates: {len(uv_coords)} UVs")\n\n                # Load material and texture info if available\n                mat_name = safe_get_array(\'material_name\')\n                if mat_name is not None:\n                    material_name = str(mat_name)\n                tex_path = safe_get_array(\'texture_path\')\n                if tex_path is not None:\n                    texture_path = str(tex_path)\n\n                # Load texture data if available\n                # Note: texture fields may be 0-d string scalars, handle them specially\n                if \'texture_data_base64\' in preprocess_data:\n                    tex_data = preprocess_data[\'texture_data_base64\']\n                    # Handle both 0-d scalar and regular arrays\n                    if hasattr(tex_data, \'item\'):\n                        tex_str = tex_data.item() if tex_data.ndim == 0 else str(tex_data)\n                    else:\n                        tex_str = str(tex_data)\n\n                    if len(tex_str) > 0:\n                        texture_data_base64 = tex_str\n\n                        # Load texture metadata (also handle 0-d scalars)\n                        if \'texture_format\' in preprocess_data:\n                            fmt = preprocess_data[\'texture_format\']\n                            texture_format = fmt.item() if hasattr(fmt, \'item\') and fmt.ndim == 0 else str(fmt)\n                        if \'texture_width\' in preprocess_data:\n                            w = preprocess_data[\'texture_width\']\n                            texture_width = int(w.item() if hasattr(w, \'item\') and w.ndim == 0 else w)\n                        if \'texture_height\' in preprocess_data:\n                            h = preprocess_data[\'texture_height\']\n                            texture_height = int(h.item() if hasattr(h, \'item\') and h.ndim == 0 else h)\n\n                        log.info(f"Loaded texture: {texture_width}x{texture_height} {texture_format} ({len(texture_data_base64) // 1024}KB base64)")\n\n                # Close npz file to release handle (required for Windows temp cleanup)\n                preprocess_data.close()\n            else:\n                # Fallback: use trimesh data\n                mesh_vertices_original = np.array(trimesh.vertices, dtype=np.float32)\n                mesh_faces = np.array(trimesh.faces, dtype=np.int32)\n                vertex_normals = np.array(trimesh.vertex_normals, dtype=np.float32) if hasattr(trimesh, \'vertex_normals\') else None\n                face_normals = np.array(trimesh.face_normals, dtype=np.float32) if hasattr(trimesh, \'face_normals\') else None\n\n            # Normalize mesh to [-1, 1]\n            mesh_bounds_min = mesh_vertices_original.min(axis=0)\n            mesh_bounds_max = mesh_vertices_original.max(axis=0)\n            mesh_center = (mesh_bounds_min + mesh_bounds_max) / 2\n            mesh_extents = mesh_bounds_max - mesh_bounds_min\n            mesh_scale = mesh_extents.max() / 2\n\n            # Normalize mesh vertices to [-1, 1]\n            mesh_vertices = (mesh_vertices_original - mesh_center) / mesh_scale\n\n            log.info("Original mesh bounds: min=%s, max=%s", mesh_bounds_min, mesh_bounds_max)\n            log.info("Mesh scale: %.4f, extents: %s", mesh_scale, mesh_extents)\n            log.info(f"Normalized mesh bounds: min={mesh_vertices.min(axis=0)}, max={mesh_vertices.max(axis=0)}")\n\n            # Create trimesh object from normalized mesh data\n            normalized_mesh = Trimesh(\n                vertices=mesh_vertices,\n                faces=mesh_faces,\n                process=True\n            )\n            log.info(f"Created normalized mesh: {len(mesh_vertices)} vertices, {len(mesh_faces)} faces")\n\n            # Build parents list from bone_parents\n            if skeleton_bone_parents is not None:\n                bone_parents = skeleton_bone_parents\n                num_bones = len(bone_parents)\n                parents_list = [None if (p is None or p == -1) else int(p) for p in bone_parents]\n\n                # Get bone names from direct inference\n                if skeleton_bone_names is not None:\n                    if isinstance(skeleton_bone_names, np.ndarray):\n                        names_list = [str(name) for name in skeleton_bone_names]\n                    elif isinstance(skeleton_bone_names, list):\n                        names_list = [str(name) for name in skeleton_bone_names]\n                    else:\n                        names_list = [f"bone_{i}" for i in range(num_bones)]\n                    log.info(f"[OK] Using {len(names_list)} model-generated bone names")\n                    # Debug: show first few bone names to diagnose naming issues\n                    log.info(f"First 5 bone names: {names_list[:5]}")\n                else:\n                    names_list = [f"bone_{i}" for i in range(num_bones)]\n                    log.info(f"Using {len(names_list)} generic bone names (model returned no names)")\n\n                # Map bones to their head joint positions\n                if skeleton_bone_to_head is not None:\n                    bone_to_head = skeleton_bone_to_head\n                    bone_joints = np.array([all_joints[bone_to_head[i]] for i in range(num_bones)])\n                else:\n                    bone_joints = all_joints[:num_bones]\n\n                # Compute tails\n                tails = np.zeros((num_bones, 3))\n                for i in range(num_bones):\n                    children = [j for j, p in enumerate(parents_list) if p == i]\n                    if children:\n                        tails[i] = np.mean([bone_joints[c] for c in children], axis=0)\n                    else:\n                        if parents_list[i] is not None:\n                            direction = bone_joints[i] - bone_joints[parents_list[i]]\n                            tails[i] = bone_joints[i] + direction * 0.3\n                        else:\n                            tails[i] = bone_joints[i] + np.array([0, 0.1, 0])\n\n            else:\n                # No hierarchy - create simple chain\n                num_bones = len(all_joints)\n                bone_joints = all_joints\n                parents_list = [None] + list(range(num_bones-1))\n                names_list = [f"bone_{i}" for i in range(num_bones)]\n\n                tails = np.zeros_like(bone_joints)\n                for i in range(num_bones):\n                    children = [j for j, p in enumerate(parents_list) if p == i]\n                    if children:\n                        tails[i] = np.mean([bone_joints[c] for c in children], axis=0)\n                    else:\n                        if parents_list[i] is not None:\n                            direction = bone_joints[i] - bone_joints[parents_list[i]]\n                            tails[i] = bone_joints[i] + direction * 0.3\n                        else:\n                            tails[i] = bone_joints[i] + np.array([0, 0.1, 0])\n\n            # Remap bone names if mixamo was requested (applies to both branches above)\n            if remap_to_mixamo:\n                remapped_names = []\n                remapped_count = 0\n                for name in names_list:\n                    if name in VROID_TO_MIXAMO_BONE_MAP:\n                        remapped_names.append(VROID_TO_MIXAMO_BONE_MAP[name])\n                        remapped_count += 1\n                    else:\n                        remapped_names.append(name)  # Keep original if not in map\n                names_list = remapped_names\n                log.info(f"Remapped {remapped_count}/{len(names_list)} bones to Mixamo naming")\n                log.info(f"First 5 names after remap: {names_list[:5]}")\n\n            # Convert to SMPL skeleton if requested (filter 52 VRoid bones to 22 SMPL joints)\n            if remap_to_smpl:\n                log.info("Converting to SMPL skeleton (22 joints)...")\n\n                # Build VRoid name -> index mapping from current skeleton\n                vroid_name_to_idx = {name: i for i, name in enumerate(names_list)}\n\n                # Filter to only SMPL joints (22 out of 52)\n                smpl_joints = []\n                missing_joints = []\n\n                for smpl_name in SMPL_JOINT_NAMES:\n                    # Find corresponding VRoid bone name\n                    vroid_name = None\n                    for vn, sn in VROID_TO_SMPL_BONE_MAP.items():\n                        if sn == smpl_name:\n                            vroid_name = vn\n                            break\n\n                    if vroid_name and vroid_name in vroid_name_to_idx:\n                        idx = vroid_name_to_idx[vroid_name]\n                        smpl_joints.append(bone_joints[idx])\n                    else:\n                        missing_joints.append(smpl_name)\n                        # Use zero position as fallback (shouldn\'t happen)\n                        smpl_joints.append(np.array([0, 0, 0]))\n\n                if missing_joints:\n                    log.warning("Warning: Missing VRoid bones for SMPL joints: %s", missing_joints)\n\n                # Replace with SMPL data\n                bone_joints = np.array(smpl_joints)\n                names_list = list(SMPL_JOINT_NAMES)\n                parents_list = [None if p == -1 else p for p in SMPL_PARENTS]\n\n                # Compute tails using CANONICAL SMPL bone directions (for symmetric rest pose)\n                # This ensures left/right bones have mirrored orientations\n                num_smpl_joints = len(SMPL_JOINT_NAMES)\n                tails = np.zeros((num_smpl_joints, 3))\n\n                for i, joint_name in enumerate(SMPL_JOINT_NAMES):\n                    # Get canonical bone direction\n                    direction = np.array(SMPL_BONE_DIRECTIONS.get(joint_name, [0, 1, 0]))\n\n                    # Compute bone length from child distance or use default\n                    children = [j for j, p in enumerate(parents_list) if p == i]\n                    if children:\n                        # Use distance to first child as bone length\n                        child_idx = children[0]\n                        bone_length = np.linalg.norm(bone_joints[child_idx] - bone_joints[i])\n                        if bone_length < 0.01:\n                            bone_length = SMPL_DEFAULT_BONE_LENGTH\n                    else:\n                        # Leaf bone - use default length\n                        bone_length = SMPL_DEFAULT_BONE_LENGTH\n\n                    # Tail = head + direction * length\n                    tails[i] = bone_joints[i] + direction * bone_length\n\n                log.info(f"Converted to SMPL: {len(names_list)} joints with canonical bone orientations")\n\n                # === STEP 1: Detect current facing direction and rotate to SMPL standard ===\n                # SMPL standard (before Y-up conversion): facing -Y, lateral along X, up along Z\n                # We need to detect current orientation and rotate to match\n\n                # Get shoulder positions to determine lateral axis\n                l_shoulder_idx = names_list.index(\'L_Shoulder\')\n                r_shoulder_idx = names_list.index(\'R_Shoulder\')\n                pelvis_idx = names_list.index(\'Pelvis\')\n                head_idx = names_list.index(\'Head\') if \'Head\' in names_list else names_list.index(\'Neck\')\n\n                l_shoulder = bone_joints[l_shoulder_idx]\n                r_shoulder = bone_joints[r_shoulder_idx]\n                pelvis = bone_joints[pelvis_idx]\n                head = bone_joints[head_idx]\n\n                # Compute current orientation vectors\n                shoulder_vec = r_shoulder - l_shoulder  # Left to Right\n                spine_vec = head - pelvis  # Up direction\n\n                # Normalize\n                shoulder_vec = shoulder_vec / (np.linalg.norm(shoulder_vec) + 1e-8)\n                spine_vec = spine_vec / (np.linalg.norm(spine_vec) + 1e-8)\n\n                # Forward = cross(right, up) for right-handed system\n                forward_vec = np.cross(shoulder_vec, spine_vec)\n                forward_vec = forward_vec / (np.linalg.norm(forward_vec) + 1e-8)\n\n                log.info("Current orientation - Lateral: %s, Up: %s, Forward: %s", shoulder_vec, spine_vec, forward_vec)\n\n                # Determine which axis is lateral (should be X for SMPL)\n                # In Blender Z-up, SMPL standard is: lateral=X, up=Z, forward=-Y\n                lateral_axis = np.argmax(np.abs(shoulder_vec))\n                up_axis = np.argmax(np.abs(spine_vec))\n\n                # Check if we need to rotate around Z axis to align lateral with X\n                if lateral_axis == 0:\n                    # Already aligned with X\n                    log.info("Lateral axis already aligned with X")\n                    z_rotation_angle = 0\n                elif lateral_axis == 1:\n                    # Lateral is along Y, need to rotate 90 degrees around Z\n                    z_rotation_angle = np.pi / 2 if shoulder_vec[1] > 0 else -np.pi / 2\n                    log.info(f"Rotating {np.degrees(z_rotation_angle):.0f} degrees around Z to align lateral with X")\n                else:\n                    # Lateral is along Z (our current case), need to rotate around up axis\n                    # This shouldn\'t happen in Z-up Blender coords, but handle it\n                    z_rotation_angle = 0\n                    log.info("Unusual: Lateral along Z axis")\n\n                # For the current mesh: lateral is along Y (in original coords), up is along Z\n                # After Z-up to Y-up conversion, this becomes: lateral along Y, up along Y - wrong!\n                # We need to rotate so lateral is along X before the conversion\n\n                # Actually, let\'s detect more carefully:\n                # If shoulders differ mainly in Y, we need 90 degree rotation around Z\n                if abs(shoulder_vec[1]) > abs(shoulder_vec[0]) and abs(shoulder_vec[1]) > 0.5:\n                    # Lateral is along Y, rotate 90 degrees around Z\n                    cos_a, sin_a = 0, 1  # 90 degrees\n                    if shoulder_vec[1] < 0:\n                        sin_a = -1  # -90 degrees\n\n                    def rotate_around_z(points):\n                        """Rotate points 90 degrees around Z axis"""\n                        rotated = np.zeros_like(points)\n                        rotated[..., 0] = cos_a * points[..., 0] - sin_a * points[..., 1]\n                        rotated[..., 1] = sin_a * points[..., 0] + cos_a * points[..., 1]\n                        rotated[..., 2] = points[..., 2]\n                        return rotated\n\n                    log.info("Rotating 90 degrees around Z to align shoulders with X axis")\n                    bone_joints = rotate_around_z(bone_joints)\n                    tails = rotate_around_z(tails)\n                    mesh_vertices = rotate_around_z(mesh_vertices)\n                    vertex_normals = rotate_around_z(vertex_normals)\n                    face_normals = rotate_around_z(face_normals)\n\n                # === STEP 2: Rotate from Blender Z-up to SMPL Y-up ===\n                # This is a -90 degree rotation around X axis: (x, y, z) -> (x, z, -y)\n                # SMPL uses: X=right, Y=up, Z=back\n                # Blender uses: X=right, Y=forward, Z=up\n                def rotate_to_smpl_coords(points):\n                    """Rotate points from Blender coords (Z-up) to SMPL coords (Y-up)"""\n                    rotated = np.zeros_like(points)\n                    rotated[..., 0] = points[..., 0]   # X stays X\n                    rotated[..., 1] = points[..., 2]   # Z becomes Y (up)\n                    rotated[..., 2] = -points[..., 1]  # -Y becomes Z (back)\n                    return rotated\n\n                # Rotate joints, tails, mesh vertices, and normals\n                bone_joints = rotate_to_smpl_coords(bone_joints)\n                tails = rotate_to_smpl_coords(tails)\n                mesh_vertices = rotate_to_smpl_coords(mesh_vertices)\n                vertex_normals = rotate_to_smpl_coords(vertex_normals)\n                face_normals = rotate_to_smpl_coords(face_normals)\n\n                # === STEP 3: Ensure correct handedness (L_Shoulder at +X, R_Shoulder at -X) ===\n                # After rotation, check if left/right are correct\n                l_shoulder_new = bone_joints[l_shoulder_idx]\n                r_shoulder_new = bone_joints[r_shoulder_idx]\n\n                # In SMPL, L_Shoulder should have positive X, R_Shoulder negative X\n                if l_shoulder_new[0] < r_shoulder_new[0]:\n                    # Left/Right are swapped, need to mirror along X\n                    log.info("Mirroring along X to fix left/right")\n                    bone_joints[..., 0] = -bone_joints[..., 0]\n                    tails[..., 0] = -tails[..., 0]\n                    mesh_vertices[..., 0] = -mesh_vertices[..., 0]\n                    vertex_normals[..., 0] = -vertex_normals[..., 0]\n                    face_normals[..., 0] = -face_normals[..., 0]\n                    # Also need to flip face winding\n                    mesh_faces = mesh_faces[:, ::-1]\n\n                # Update mesh bounds after rotation\n                mesh_bounds_min = mesh_vertices.min(axis=0)\n                mesh_bounds_max = mesh_vertices.max(axis=0)\n                mesh_center = (mesh_bounds_min + mesh_bounds_max) / 2\n\n                log.info("Rotated to SMPL Y-up coordinate system")\n\n            # Save as RawData NPZ for skinning phase\n            persistent_npz = os.path.join(_unirig_temp_directory(), f"skeleton_{seed}.npz")\n            np.savez(\n                persistent_npz,\n                vertices=mesh_vertices,\n                vertex_normals=vertex_normals,\n                faces=mesh_faces,\n                face_normals=face_normals,\n                joints=bone_joints,\n                tails=tails,\n                parents=np.array(parents_list, dtype=object),\n                names=np.array(names_list, dtype=object),\n                uv_coords=uv_coords if uv_coords is not None else np.array([], dtype=np.float32),\n                uv_faces=uv_faces if uv_faces is not None else np.array([], dtype=np.int32),\n                material_name=material_name if material_name else "",\n                texture_path=texture_path if texture_path else "",\n                mesh_bounds_min=mesh_bounds_min,\n                mesh_bounds_max=mesh_bounds_max,\n                mesh_center=mesh_center,\n                mesh_scale=mesh_scale,\n                skin=None,\n                no_skin=None,\n                matrix_local=None,\n                path=None,\n                cls=cls_value\n            )\n            log.info("Saved skeleton NPZ to: %s", persistent_npz)\n\n            # Build skeleton dict with ALL data\n            skeleton = {\n                "vertices": all_joints,\n                "edges": edges,\n                "joints": bone_joints,\n                "tails": tails,\n                "names": names_list,\n                "parents": parents_list,\n                "mesh_vertices": mesh_vertices,\n                "mesh_faces": mesh_faces,\n                "mesh_vertex_normals": vertex_normals,\n                "mesh_face_normals": face_normals,\n                "uv_coords": uv_coords,\n                "uv_faces": uv_faces,\n                "material_name": material_name,\n                "texture_path": texture_path,\n                "texture_data_base64": texture_data_base64,\n                "texture_format": texture_format,\n                "texture_width": texture_width,\n                "texture_height": texture_height,\n                "mesh_bounds_min": mesh_bounds_min,\n                "mesh_bounds_max": mesh_bounds_max,\n                "mesh_center": mesh_center,\n                "mesh_scale": mesh_scale,\n                "is_normalized": True,\n                "skeleton_npz_path": persistent_npz,\n                "bone_names": names_list,\n                "bone_parents": parents_list,\n                "output_format": original_template,\n            }\n\n            if skeleton_bone_to_head is not None:\n                skeleton[\'bone_to_head_vertex\'] = skeleton_bone_to_head.tolist()\n\n            # Note: skeleton_data NPZ file was already closed immediately after extraction\n            # to avoid Windows file locking issues during temp cleanup\n\n            log.info(f"Included hierarchy: {len(names_list)} bones with parent relationships")\n\n            # Create texture preview output\n            if texture_data_base64:\n                texture_preview, tex_w, tex_h = decode_texture_to_comfy_image(texture_data_base64)\n                if texture_preview is not None:\n                    log.info("Texture preview created: %sx%s", tex_w, tex_h)\n                else:\n                    log.warning("Warning: Could not decode texture for preview")\n                    texture_preview = create_placeholder_texture()\n            else:\n                log.info("No texture available for preview")\n                texture_preview = create_placeholder_texture()\n\n            total_time = time.time() - total_start\n            log.info("Skeleton extraction complete!")\n            log.info("TOTAL TIME: %.2fs", total_time)\n            return (normalized_mesh, skeleton, texture_preview)\n',
    'skinning.py': '# UNIRIG_SKINNING_FOLDER_PATHS_SAFE_UNIQUE_OUTPUT_V2\n"""\nSkinning nodes for UniRig - Apply skinning weights using ML models.\n\nUses comfy-env isolated environment for GPU dependencies.\nUses direct Python inference with bpy for FBX export.\n"""\n\nimport logging\nimport os\nimport sys\nimport tempfile\nimport shutil\nimport numpy as np\nimport time\n\ntry:\n    import folder_paths\nexcept Exception:\n    folder_paths = None\n\nlog = logging.getLogger("unirig")\n\n# Support both relative imports (ComfyUI) and absolute imports (testing)\ntry:\n    from .base import (\n        UNIRIG_MODELS_DIR,\n        decode_texture_to_comfy_image,\n        create_placeholder_texture,\n    )\nexcept ImportError:\n    from base import (\n        UNIRIG_MODELS_DIR,\n        decode_texture_to_comfy_image,\n        create_placeholder_texture,\n    )\n\n# Direct FBX export module (bpy as Python module)\ntry:\n    from .unirig import direct_export_fbx as _direct_export_module\nexcept Exception as e:\n    log.info("Direct FBX export not available: %s", e)\n    _direct_export_module = None\n\n# Direct inference module\ntry:\n    from .unirig import direct as _direct_inference_module\nexcept Exception as e:\n    log.info("Direct inference not available: %s", e)\n    _direct_inference_module = None\n\n\ndef _get_direct_export():\n    """Get the direct FBX export module for in-process export using bpy."""\n    return _direct_export_module\n\n\ndef _get_direct_inference():\n    """Get the direct inference module for in-process model inference."""\n    return _direct_inference_module\n\n\nclass UniRigApplySkinningMLNew:\n    """\n    Apply skinning weights using ML.\n\n    Takes skeleton dict and mesh, prepares data and runs ML inference.\n\n    Runs in isolated environment with GPU dependencies.\n    Requires pre-loaded model from UniRigLoadSkinningModel.\n    """\n\n    @classmethod\n    def INPUT_TYPES(cls):\n        return {\n            "required": {\n                "normalized_mesh": ("TRIMESH",),\n                "skeleton": ("SKELETON",),\n                "skinning_model": ("UNIRIG_SKINNING_MODEL", {\n                    "tooltip": "Pre-loaded skinning model (from UniRigLoadSkinningModel) - REQUIRED"\n                }),\n            },\n            "optional": {\n                "fbx_name": ("STRING", {\n                    "default": "",\n                    "tooltip": "Custom filename for saved FBX (without extension). If empty, uses rigged_<timestamp>.fbx"\n                }),\n                "voxel_grid_size": ("INT", {\n                    "default": 196,\n                    "min": 64,\n                    "max": 512,\n                    "step": 64,\n                    "tooltip": "Voxel grid resolution for spatial weight distribution. Higher = better quality, more VRAM. Default: 196 (model trained with this)"\n                }),\n                "num_samples": ("INT", {\n                    "default": 32768,\n                    "min": 8192,\n                    "max": 131072,\n                    "step": 8192,\n                    "tooltip": "Number of surface samples for weight calculation. Higher = more accurate, slower. Default: 32768"\n                }),\n                "vertex_samples": ("INT", {\n                    "default": 8192,\n                    "min": 2048,\n                    "max": 32768,\n                    "step": 2048,\n                    "tooltip": "Number of vertex samples. Higher = more accurate vertex processing. Default: 8192"\n                }),\n                "voxel_mask_power": ("FLOAT", {\n                    "default": 0.5,\n                    "min": 0.1,\n                    "max": 5.0,\n                    "step": 0.1,\n                    "tooltip": "Power for voxel mask weight sharpness (alpha). Lower = smoother transitions. Default: 0.5 (model trained with this)"\n                }),\n            }\n        }\n\n    RETURN_TYPES = ("STRING", "IMAGE")\n    RETURN_NAMES = ("fbx_output_path", "texture_preview")\n    FUNCTION = "apply_skinning"\n    CATEGORY = "UniRig"\n\n    def apply_skinning(self, normalized_mesh, skeleton, skinning_model,\n                       fbx_name=None, voxel_grid_size=None, num_samples=None, vertex_samples=None,\n                       voxel_mask_power=None):\n        log.info(f"Starting ML skinning (cached model only)...")\n\n        # Validate model is provided\n        if skinning_model is None:\n            raise RuntimeError(\n                "skinning_model is required for UniRigApplySkinningMLNew. "\n                "Please connect a UniRigLoadSkinningModel node."\n            )\n\n        # Validate model has checkpoint path\n        if not skinning_model.get("checkpoint_path"):\n            raise RuntimeError(\n                "skinning_model checkpoint not found. "\n                "Please connect a UniRigLoadSkinningModel node."\n            )\n\n        log.info(f"Using pre-loaded cached model")\n        task_config_path = skinning_model.get("task_config_path")\n\n        # Create temporary directory\n        temp_dir = tempfile.mkdtemp(prefix="unirig_skinning_new_")\n        predict_skeleton_dir = os.path.join(temp_dir, "input")\n        os.makedirs(predict_skeleton_dir, exist_ok=True)\n\n        # Prepare skeleton NPZ from dict\n        predict_skeleton_path = os.path.join(predict_skeleton_dir, "predict_skeleton.npz")\n        save_data = {\n            \'joints\': skeleton[\'joints\'],\n            \'names\': skeleton[\'names\'],\n            \'parents\': skeleton[\'parents\'],\n            \'tails\': skeleton[\'tails\'],\n        }\n\n        # Add mesh data\n        mesh_data_mapping = {\n            \'mesh_vertices\': \'vertices\',\n            \'mesh_faces\': \'faces\',\n            \'mesh_vertex_normals\': \'vertex_normals\',\n            \'mesh_face_normals\': \'face_normals\',\n        }\n        for skel_key, npz_key in mesh_data_mapping.items():\n            if skel_key in skeleton:\n                save_data[npz_key] = skeleton[skel_key]\n\n        # Add optional RawData fields\n        save_data[\'skin\'] = None\n        save_data[\'no_skin\'] = None\n        save_data[\'matrix_local\'] = skeleton.get(\'matrix_local\')\n        save_data[\'path\'] = None\n        save_data[\'cls\'] = skeleton.get(\'cls\')\n\n        # Add UV data if available\n        if skeleton.get(\'uv_coords\') is not None:\n            save_data[\'uv_coords\'] = skeleton[\'uv_coords\']\n            save_data[\'uv_faces\'] = skeleton.get(\'uv_faces\')\n            log.info(f"UV data included: {len(skeleton[\'uv_coords\'])} UVs")\n        else:\n            save_data[\'uv_coords\'] = np.array([], dtype=np.float32)\n            save_data[\'uv_faces\'] = np.array([], dtype=np.int32)\n\n        # Add texture data if available\n        if skeleton.get(\'texture_data_base64\') is not None:\n            save_data[\'texture_data_base64\'] = skeleton[\'texture_data_base64\']\n            save_data[\'texture_format\'] = skeleton.get(\'texture_format\', \'PNG\')\n            save_data[\'texture_width\'] = skeleton.get(\'texture_width\', 0)\n            save_data[\'texture_height\'] = skeleton.get(\'texture_height\', 0)\n            save_data[\'material_name\'] = skeleton.get(\'material_name\', \'\')\n            log.info(f"Texture data included: {skeleton[\'texture_width\']}x{skeleton[\'texture_height\']} {skeleton[\'texture_format\']}")\n        else:\n            save_data[\'texture_data_base64\'] = ""\n            save_data[\'texture_format\'] = ""\n            save_data[\'texture_width\'] = 0\n            save_data[\'texture_height\'] = 0\n            save_data[\'material_name\'] = skeleton.get(\'material_name\', \'\')\n\n        np.savez(predict_skeleton_path, **save_data)\n        log.info(f"Prepared skeleton NPZ: {predict_skeleton_path}")\n\n        # Export mesh to GLB\n        input_glb = os.path.join(temp_dir, "input.glb")\n\n        normalized_mesh.export(input_glb)\n        log.info(f"Exported mesh: {normalized_mesh.vertices.shape[0]} vertices, {normalized_mesh.faces.shape[0]} faces")\n\n        # Run skinning inference\n        step_start = time.time()\n        output_fbx = os.path.join(temp_dir, "rigged.fbx")\n\n        # Build config overrides from optional parameters\n        config_overrides = {}\n        if voxel_grid_size is not None:\n            config_overrides[\'voxel_grid_size\'] = voxel_grid_size\n        if num_samples is not None:\n            config_overrides[\'num_samples\'] = num_samples\n        if vertex_samples is not None:\n            config_overrides[\'vertex_samples\'] = vertex_samples\n        if voxel_mask_power is not None:\n            config_overrides[\'voxel_mask_power\'] = voxel_mask_power\n\n        if config_overrides:\n            log.info(f"Config overrides: {config_overrides}")\n\n        # Run direct inference (no subprocess)\n        log.info(f"Running skinning inference with direct inference...")\n        direct_module = _get_direct_inference()\n        if not direct_module:\n            raise RuntimeError("Direct inference module not available. Check installation.")\n\n        # Get checkpoint path from skinning_model\n        checkpoint_path = skinning_model.get("checkpoint_path")\n        if not checkpoint_path:\n            # Fallback: use default path\n            checkpoint_path = os.path.join(UNIRIG_MODELS_DIR, "skin.safetensors")\n\n        if not os.path.exists(checkpoint_path):\n            raise RuntimeError(f"Skinning checkpoint not found: {checkpoint_path}")\n\n        log.info(f"Using checkpoint: {checkpoint_path}")\n\n        # Get mesh data from skeleton dict or normalized_mesh\n        mesh_vertices = skeleton.get(\'mesh_vertices\')\n        if mesh_vertices is None:\n            mesh_vertices = np.array(normalized_mesh.vertices, dtype=np.float32)\n\n        mesh_normals = skeleton.get(\'mesh_vertex_normals\')\n        if mesh_normals is None:\n            mesh_normals = np.array(normalized_mesh.vertex_normals, dtype=np.float32)\n\n        joints = np.array(skeleton[\'joints\'], dtype=np.float32)\n        # Convert parent indices: None -> -1 for the model (handle before numpy conversion)\n        parents_list = skeleton[\'parents\']\n        parents = np.array([-1 if p is None else int(p) for p in parents_list], dtype=np.int64)\n\n        # Get mesh faces\n        mesh_faces = skeleton.get(\'mesh_faces\')\n        if mesh_faces is None:\n            mesh_faces = np.array(normalized_mesh.faces, dtype=np.int32)\n\n        # Get bone tails (if available)\n        tails = skeleton.get(\'tails\')\n        if tails is not None:\n            tails = np.array(tails, dtype=np.float32)\n\n        # Get voxel grid size from config overrides\n        voxel_grid_size_val = config_overrides.get(\'voxel_grid_size\', 196)\n\n        log.info(f"Mesh: {len(mesh_vertices)} vertices, {len(mesh_faces)} faces")\n        log.info(f"Skeleton: {len(joints)} joints")\n\n        # Extract dtype and attn_backend from model config (set by UniRigLoadModel)\n        model_dtype = skinning_model.get("dtype")\n        model_attn_backend = skinning_model.get("attn_backend", "auto")\n\n        # Run direct skinning prediction\n        skin_weights = direct_module.predict_skinning(\n            vertices=mesh_vertices,\n            normals=mesh_normals,\n            joints=joints,\n            parents=parents,\n            checkpoint_path=checkpoint_path,\n            faces=mesh_faces,\n            tails=tails,\n            voxel_grid_size=voxel_grid_size_val,\n            dtype=model_dtype,\n            attn_backend=model_attn_backend,\n        )\n\n        inference_time = time.time() - step_start\n        log.info(f"[OK] Direct inference completed in {inference_time:.2f}s")\n        log.info(f"Skin weights shape: {skin_weights.shape}")\n\n        # Generate FBX output using direct bpy export\n        log.info(f"Generating FBX...")\n\n        direct_export = _get_direct_export()\n        if not direct_export:\n            raise RuntimeError("Direct FBX export module not available. Check bpy installation.")\n\n        direct_export.export_rigged_fbx(\n            joints=skeleton[\'joints\'],\n            parents=[int(p) if p is not None else -1 for p in skeleton[\'parents\']],\n            names=list(skeleton[\'names\']),\n            output_fbx=output_fbx,\n            vertices=mesh_vertices,\n            faces=mesh_faces,\n            skin=skin_weights,\n            tails=skeleton.get(\'tails\'),\n            uv_coords=skeleton.get(\'uv_coords\'),\n            uv_faces=skeleton.get(\'uv_faces\'),\n            texture_data_base64=skeleton.get(\'texture_data_base64\') or \'\',\n            texture_format=skeleton.get(\'texture_format\') or \'PNG\',\n            material_name=skeleton.get(\'material_name\') or \'Material\',\n        )\n        log.info(f"[OK] FBX generated: {output_fbx}")\n\n        log.info(f"Skinning completed")\n\n        # Verify FBX output\n        fbx_path = output_fbx\n        if not os.path.exists(fbx_path):\n            raise RuntimeError(f"Skinning output FBX not found: {fbx_path}")\n\n        log.info(f"Found output FBX: {fbx_path}")\n        log.info(f"FBX file size: {os.path.getsize(fbx_path)} bytes")\n\n        # Auto-save FBX to output directory\n        if folder_paths is not None:\n            output_dir = folder_paths.get_output_directory()\n        else:\n            output_dir = os.environ.get("COMFYUI_OUTPUT_DIR") or os.path.join(os.path.expanduser("~"), "Documents", "ComfyUI", "output")\n            os.makedirs(output_dir, exist_ok=True)\n\n        # Determine output filename with skeleton template suffix.\n        # Locked installer patch: never overwrite an existing FBX.\n        template_suffix = skeleton.get(\'output_format\', \'unknown\')\n\n        def _next_fbx_filename(folder, stem):\n            folder = os.path.abspath(folder)\n            os.makedirs(folder, exist_ok=True)\n            candidate = f"{stem}.fbx"\n            if not os.path.exists(os.path.join(folder, candidate)):\n                return candidate\n            index = 1\n            while True:\n                candidate = f"{stem}_{index:03d}.fbx"\n                if not os.path.exists(os.path.join(folder, candidate)):\n                    return candidate\n                index += 1\n\n        if fbx_name and fbx_name.strip():\n            base_name = fbx_name.strip()\n            if base_name.lower().endswith(\'.fbx\'):\n                base_name = base_name[:-4]\n            output_stem = f"{base_name}_{template_suffix}"\n        else:\n            output_stem = f"rigged_{template_suffix}"\n\n        output_filename = _next_fbx_filename(output_dir, output_stem)\n        output_path = os.path.join(output_dir, output_filename)\n        shutil.copy(fbx_path, output_path)\n\n        log.info(f"Auto-saved FBX to output: {output_filename}")\n        log.info(f"Full path: {output_path}")\n\n        # Create texture preview output\n        texture_preview = None\n        if skeleton.get(\'texture_data_base64\'):\n            texture_preview, tex_w, tex_h = decode_texture_to_comfy_image(skeleton[\'texture_data_base64\'])\n            if texture_preview is not None:\n                log.info(f"Texture preview created: {tex_w}x{tex_h}")\n            else:\n                log.warning(f"Could not decode texture for preview")\n                texture_preview = create_placeholder_texture()\n        else:\n            log.info(f"No texture available for preview")\n            texture_preview = create_placeholder_texture()\n\n        log.info(f"Skinning application complete!")\n\n        # Clean up temporary directory\n        # Windows-specific: Force garbage collection and retry logic to release file handles\n        # This helps prevent "file in use by another process" errors during cleanup\n        if sys.platform == \'win32\':\n            import gc\n            gc.collect()\n            # Give Windows a moment to release file handles\n            time.sleep(0.1)\n\n        try:\n            # First attempt with ignore_errors\n            shutil.rmtree(temp_dir, ignore_errors=True)\n            log.info(f"Cleaned up temp directory")\n        except Exception as e:\n            # Don\'t fail the whole operation if cleanup fails\n            log.warning(f"Could not clean up temp directory: {e}")\n\n        # Windows: If directory still exists, schedule for deletion on restart\n        if sys.platform == \'win32\' and os.path.exists(temp_dir):\n            log.info(f"Temp directory will be cleaned on next restart: {temp_dir}")\n\n        return (output_filename, texture_preview)\n',
    'skeleton_io.py': '# UNIRIG_SKELETON_IO_PREVIEW_COPY_V2\n"""\nSkeleton I/O nodes for UniRig - Save, Load, and Preview operations.\n"""\n\nimport os\nimport numpy as np\nimport time\nimport shutil\nimport pickle\nimport json\nfrom pathlib import Path\nimport logging\n\ntry:\n    import folder_paths\nexcept Exception:\n    folder_paths = None\n\n\ndef _get_input_directory():\n    """Return ComfyUI input directory without crashing during comfy-env metadata scan."""\n    if folder_paths is not None:\n        try:\n            return folder_paths.get_input_directory()\n        except Exception:\n            pass\n\n    # Desktop Local fallback\n    return os.path.join(str(Path.home()), "Documents", "ComfyUI", "input")\n\n\ndef _get_output_directory():\n    """Return the output directory served by ComfyUI when available."""\n    if folder_paths is not None:\n        try:\n            return folder_paths.get_output_directory()\n        except Exception:\n            pass\n\n    # Desktop Local / fallback candidates\n    candidates = [\n        os.path.join(str(Path.home()), "Documents", "ComfyUI", "output"),\n        r"D:\\ComfyUI_Local\\resources\\ComfyUI\\output",\n    ]\n    for p in candidates:\n        if os.path.exists(p):\n            return p\n    return candidates[0]\n\n\ndef _safe_preview_filename(src_path):\n    """Copy a file into ComfyUI\'s served output folder with a non-destructive filename."""\n    output_dir = _get_output_directory()\n    os.makedirs(output_dir, exist_ok=True)\n\n    src_path = os.path.abspath(src_path)\n    base = os.path.basename(src_path)\n    stem, ext = os.path.splitext(base)\n    if not ext:\n        ext = ".fbx"\n\n    dst_path = os.path.join(output_dir, base)\n\n    # If already in the served output folder, keep the existing filename.\n    try:\n        if os.path.abspath(os.path.dirname(src_path)) == os.path.abspath(output_dir):\n            return base\n    except Exception:\n        pass\n\n    # Never overwrite an existing preview file.\n    if os.path.exists(dst_path):\n        dst_path = os.path.join(output_dir, f"{stem}_preview_{int(time.time())}{ext}")\n\n    shutil.copy2(src_path, dst_path)\n    log.info("Copied FBX for preview: %s", dst_path)\n    return os.path.basename(dst_path)\n\nlog = logging.getLogger("unirig")\n\ntry:\n    from .base import NODE_DIR\nexcept ImportError:\n    from base import NODE_DIR\n\n# Direct bone debug extraction module (bpy as Python module)\ntry:\n    from .unirig import direct_extract_bone_debug as _direct_bone_debug_module\nexcept Exception as e:\n    log.debug("Direct bone debug not available: %s", e)\n    _direct_bone_debug_module = None\n\n\ndef _get_direct_bone_debug():\n    """Get the direct bone debug extraction module for in-process extraction using bpy."""\n    return _direct_bone_debug_module\n\n\nclass UniRigLoadRiggedMesh:\n    """\n    Load a rigged FBX file from disk.\n\n    Loads existing FBX files with rigging/skeleton data, allowing you to\n    preview and work with pre-rigged models.\n    """\n\n    @classmethod\n    def INPUT_TYPES(cls):\n        input_files = cls.get_fbx_files_from_input()\n        output_files = cls.get_fbx_files_from_output()\n        all_files = sorted(set(input_files + output_files)) or [""]\n\n        return {\n            "required": {\n                "fbx_file": (all_files, {"file_upload": True}),\n            },\n        }\n\n    RETURN_TYPES = ("STRING", "STRING")\n    RETURN_NAMES = ("fbx_output_path", "info")\n    FUNCTION = "load"\n    CATEGORY = "unirig"\n\n    @classmethod\n    def get_fbx_files_from_input(cls):\n        """Get list of available FBX files in input folder."""\n        fbx_files = []\n        input_dir = _get_input_directory()\n\n        if input_dir is not None and os.path.exists(input_dir):\n            for root, dirs, files in os.walk(input_dir):\n                for file in files:\n                    if file.lower().endswith(\'.fbx\'):\n                        rel_path = os.path.relpath(os.path.join(root, file), input_dir)\n                        rel_path = rel_path.replace(os.sep, \'/\')  # Normalize to forward slashes for cross-platform\n                        fbx_files.append(rel_path)\n\n        return sorted(fbx_files)\n\n    @classmethod\n    def get_fbx_files_from_output(cls):\n        """Get list of available FBX files in output folder."""\n        fbx_files = []\n        output_dir = _get_output_directory()\n\n        if output_dir is not None and os.path.exists(output_dir):\n            for root, dirs, files in os.walk(output_dir):\n                for file in files:\n                    if file.lower().endswith(\'.fbx\'):\n                        rel_path = os.path.relpath(os.path.join(root, file), output_dir)\n                        rel_path = rel_path.replace(os.sep, \'/\')  # Normalize to forward slashes for cross-platform\n                        fbx_files.append(rel_path)\n\n        return sorted(fbx_files)\n\n    def load(self, fbx_file):\n        """Load an FBX file and return its filename in output directory."""\n        log.info("Loading FBX file: %s", fbx_file)\n\n        if not fbx_file:\n            raise RuntimeError("No FBX file specified. Please select or upload an FBX file.")\n\n        # Search in both input and output directories\n        input_dir = _get_input_directory()\n        output_dir = _get_output_directory()\n\n        input_path = os.path.join(input_dir, fbx_file)\n        output_path = os.path.join(output_dir, fbx_file)\n\n        # Find the file\n        if os.path.exists(output_path):\n            fbx_path = output_path\n            source = "output"\n        elif os.path.exists(input_path):\n            fbx_path = input_path\n            source = "input"\n        else:\n            raise RuntimeError(f"FBX file not found: {fbx_file}")\n\n        # If loading from input, copy to output directory\n        if source == "input":\n            output_filename = f"loaded_{int(time.time())}_{os.path.basename(fbx_file)}"\n            final_output_path = os.path.join(output_dir, output_filename)\n            shutil.copy(fbx_path, final_output_path)\n            log.info("Copied from input to output: %s", output_filename)\n        else:\n            output_filename = fbx_file\n            final_output_path = output_path\n            log.info("Using existing file from output: %s", output_filename)\n\n        # Extract mesh info using bpy\n        mesh_info = {}\n        try:\n            import bpy\n            bpy.ops.wm.read_factory_settings(use_empty=True)\n            bpy.ops.import_scene.fbx(filepath=fbx_path)\n\n            mesh_objects = [obj for obj in bpy.data.objects if obj.type == \'MESH\']\n            total_vertices = sum(len(obj.data.vertices) for obj in mesh_objects)\n            total_faces = sum(len(obj.data.polygons) for obj in mesh_objects)\n\n            if mesh_objects:\n                import mathutils\n                all_verts = []\n                for obj in mesh_objects:\n                    for v in obj.data.vertices:\n                        all_verts.append(obj.matrix_world @ v.co)\n                all_verts = np.array(all_verts)\n                bbox_min = all_verts.min(axis=0).tolist()\n                bbox_max = all_verts.max(axis=0).tolist()\n                extents = (all_verts.max(axis=0) - all_verts.min(axis=0)).tolist()\n            else:\n                bbox_min = bbox_max = extents = [0, 0, 0]\n\n            mesh_info = {\n                "type": "Scene" if len(mesh_objects) > 1 else "Mesh",\n                "mesh_count": len(mesh_objects),\n                "total_vertices": total_vertices,\n                "total_faces": total_faces,\n                "bbox_min": bbox_min,\n                "bbox_max": bbox_max,\n                "extents": extents,\n            }\n            log.info("Mesh: %s objects, %s verts, %s faces", len(mesh_objects), total_vertices, total_faces)\n        except Exception as e:\n            log.info("Could not parse mesh geometry: %s", e)\n            mesh_info = {"type": "Unknown", "error": str(e)}\n\n        # Extract skeleton info using bpy\n        skeleton_info = {}\n        try:\n            armatures = [obj for obj in bpy.data.objects if obj.type == \'ARMATURE\']\n            if armatures:\n                arm = armatures[0]\n                bone_names = [b.name for b in arm.data.bones]\n                skeleton_info = {\n                    "num_bones": len(bone_names),\n                    "bone_names": bone_names[:10],\n                    "has_skeleton": True,\n                }\n                log.info("Found %s bones", len(bone_names))\n            else:\n                skeleton_info = {"has_skeleton": False, "note": "No armature found"}\n        except Exception as e:\n            log.info("Could not parse skeleton: %s", e)\n            skeleton_info = {"has_skeleton": "unknown", "error": str(e)}\n\n        # Create info string\n        file_size = os.path.getsize(final_output_path)\n        info_lines = [\n            f"File: {os.path.basename(fbx_file)}",\n            f"Size: {file_size / 1024:.1f} KB",\n            "",\n            "Mesh Info:",\n            f"  Type: {mesh_info.get(\'type\', \'Unknown\')}",\n            f"  Meshes: {mesh_info.get(\'mesh_count\', \'Unknown\')}",\n            f"  Vertices: {mesh_info.get(\'total_vertices\', \'Unknown\'):,}" if isinstance(mesh_info.get(\'total_vertices\'), int) else f"  Vertices: Unknown",\n            f"  Faces: {mesh_info.get(\'total_faces\', \'Unknown\'):,}" if isinstance(mesh_info.get(\'total_faces\'), int) else f"  Faces: Unknown",\n        ]\n\n        if \'extents\' in mesh_info and mesh_info[\'extents\']:\n            extents = mesh_info[\'extents\']\n            info_lines.append(f"  Mesh Size: [{extents[0]:.3f}, {extents[1]:.3f}, {extents[2]:.3f}]")\n\n        if \'bbox_min\' in mesh_info and \'bbox_max\' in mesh_info:\n            bbox_min = mesh_info[\'bbox_min\']\n            bbox_max = mesh_info[\'bbox_max\']\n            info_lines.append(f"  Bounding Box:")\n            info_lines.append(f"    Min: [{bbox_min[0]:.3f}, {bbox_min[1]:.3f}, {bbox_min[2]:.3f}]")\n            info_lines.append(f"    Max: [{bbox_max[0]:.3f}, {bbox_max[1]:.3f}, {bbox_max[2]:.3f}]")\n\n        info_lines.append("")\n        info_lines.append("Skeleton Info:")\n\n        if skeleton_info.get("has_skeleton"):\n            info_lines.append(f"  Bones: {skeleton_info.get(\'num_bones\', 0)}")\n            if skeleton_info.get("skeleton_extents"):\n                extents = skeleton_info[\'skeleton_extents\']\n                info_lines.append(f"  Skeleton Size: [{extents[0]:.3f}, {extents[1]:.3f}, {extents[2]:.3f}]")\n            if skeleton_info.get("bone_names"):\n                sample_bones = skeleton_info[\'bone_names\'][:5]\n                info_lines.append(f"  Sample bones: {\', \'.join(sample_bones)}")\n        else:\n            info_lines.append(f"  Status: {skeleton_info.get(\'note\', \'No skeleton detected\')}")\n\n        info_string = "\\n".join(info_lines)\n\n        log.info("Loaded successfully")\n        log.info("%s", info_string)\n\n        return (final_output_path, info_string)\n\n\nclass UniRigPreviewRiggedMesh:\n    """\n    Preview rigged mesh with interactive FBX viewer.\n\n    Displays the rigged FBX in a Three.js viewer with skeleton visualization\n    and interactive bone manipulation controls.\n    """\n\n    @classmethod\n    def INPUT_TYPES(cls):\n        return {\n            "required": {\n                "fbx_output_path": ("STRING", {\n                    "tooltip": "FBX filename from output directory (from UniRigApplySkinningMLNew or UniRigLoadRiggedMesh)"\n                }),\n            },\n        }\n\n    RETURN_TYPES = ()\n    OUTPUT_NODE = True\n    FUNCTION = "preview"\n    CATEGORY = "unirig"\n\n    def preview(self, fbx_output_path):\n        """Preview the rigged mesh in an interactive FBX viewer."""\n        log.info("Preparing preview...")\n\n        # FBX should already be in output directory\n        if os.path.isabs(fbx_output_path):\n            fbx_path = fbx_output_path\n        else:\n            output_dir = _get_output_directory()\n            fbx_path = os.path.join(output_dir, fbx_output_path)\n\n        if not os.path.exists(fbx_path):\n            raise RuntimeError(f"FBX file not found in output directory: {fbx_output_path}")\n\n        log.info("FBX path: %s", fbx_path)\n\n        # FBX is already in output, so viewer can access it directly\n        # Assume all FBX files have skinning and skeleton\n        has_skinning = True\n        has_skeleton = True\n\n        log.info("Has skinning: %s", has_skinning)\n        log.info("Has skeleton: %s", has_skeleton)\n\n        viewer_filename = _safe_preview_filename(fbx_path)\n\n        return {\n            "ui": {\n                "fbx_file": [viewer_filename],\n                "has_skinning": [bool(has_skinning)],\n                "has_skeleton": [bool(has_skeleton)],\n            }\n        }\n\n\nclass UniRigExportPosedFBX:\n    """\n    Export rigged mesh with custom bone pose to FBX.\n\n    Takes a rigged mesh and bone transform data, applies the pose,\n    and exports the result as FBX using Blender.\n    """\n\n    @classmethod\n    def INPUT_TYPES(cls):\n        return {\n            "required": {\n                "rigged_mesh": ("RIGGED_MESH",),\n                "output_filename": ("STRING", {\n                    "default": "posed_export.fbx",\n                    "tooltip": "Output filename for the posed FBX"\n                }),\n            },\n            "optional": {\n                "bone_transforms_json": ("STRING", {\n                    "default": "{}",\n                    "multiline": True,\n                    "tooltip": "JSON string containing bone transforms (name -> {position, quaternion, scale})"\n                }),\n            }\n        }\n\n    RETURN_TYPES = ("STRING",)\n    RETURN_NAMES = ("filepath",)\n    FUNCTION = "export_posed_fbx"\n    CATEGORY = "unirig"\n    OUTPUT_NODE = True\n\n    def export_posed_fbx(self, rigged_mesh, output_filename, bone_transforms_json="{}"):\n        """Export rigged mesh with custom pose to FBX using bpy directly."""\n        log.info("Exporting posed FBX...")\n\n        # Get original FBX path\n        fbx_path = rigged_mesh.get("fbx_path")\n        if not fbx_path or not os.path.exists(fbx_path):\n            raise RuntimeError(f"Rigged mesh FBX not found: {fbx_path}")\n\n        log.info("Source FBX: %s", fbx_path)\n\n        # Parse bone transforms\n        try:\n            bone_transforms = json.loads(bone_transforms_json)\n            log.info(f"Loaded transforms for {len(bone_transforms)} bones")\n        except json.JSONDecodeError as e:\n            raise ValueError(f"Invalid JSON in bone_transforms_json: {e}")\n\n        # Prepare output path\n        output_dir = _get_output_directory()\n        if not output_filename.endswith(\'.fbx\'):\n            output_filename = output_filename + \'.fbx\'\n        output_fbx_path = os.path.join(output_dir, output_filename)\n\n        # Use direct bpy export\n        try:\n            from .lib.direct_export_posed_fbx import export_posed_fbx as direct_export\n            direct_export(fbx_path, output_fbx_path, bone_transforms)\n        except ImportError as e:\n            raise RuntimeError(\n                f"Failed to import direct_export_posed_fbx: {e}\\n"\n                "Make sure bpy is available in your environment (unirig isolated environment)."\n            )\n\n        if not os.path.exists(output_fbx_path):\n            raise RuntimeError(f"Export completed but output file not found: {output_fbx_path}")\n\n        log.info("[OK] Successfully exported to: %s", output_fbx_path)\n\n        return (output_fbx_path,)\n\n\nclass UniRigViewRigging:\n    """\n    View rigging debug information.\n\n    Displays skeleton bones with names, roll/rotation values, and other\n    debugging information in an interactive 3D viewer.\n    """\n\n    @classmethod\n    def INPUT_TYPES(cls):\n        return {\n            "required": {\n                "fbx_output_path": ("STRING", {\n                    "tooltip": "FBX filename from output directory"\n                }),\n            },\n        }\n\n    RETURN_TYPES = ()\n    OUTPUT_NODE = True\n    FUNCTION = "view_rigging"\n    CATEGORY = "unirig"\n\n    def view_rigging(self, fbx_output_path):\n        """View rigging debug information for the FBX file."""\n        log.debug("Preparing debug view...")\n\n        # FBX should already be in output directory\n        output_dir = _get_output_directory()\n\n        # Handle both relative paths and absolute paths\n        if os.path.isabs(fbx_output_path):\n            fbx_path = fbx_output_path\n        else:\n            fbx_path = os.path.join(output_dir, fbx_output_path)\n\n        if not os.path.exists(fbx_path):\n            raise RuntimeError(f"FBX file not found: {fbx_output_path}")\n\n        log.info("FBX path: %s", fbx_path)\n\n        # Extract bone debug data using direct bpy module\n        bone_debug_data = None\n        bone_debug_module = _get_direct_bone_debug()\n\n        if bone_debug_module:\n            try:\n                bone_debug_data = bone_debug_module.extract_bone_debug(fbx_path)\n                log.debug(f"Extracted debug data for {bone_debug_data.get(\'bone_count\', 0)} bones")\n            except Exception as e:\n                log.warning("Warning: Could not extract bone debug data: %s", e)\n                bone_debug_data = {\'error\': str(e), \'bones\': [], \'bone_count\': 0}\n        else:\n            log.warning("Warning: bpy module not available, bone debug data will be limited")\n            bone_debug_data = {\'error\': \'bpy module not available\', \'bones\': [], \'bone_count\': 0}\n\n        # Return data for the viewer widget\n        # For relative path, just use the filename for the viewer\n        if os.path.isabs(fbx_output_path):\n            viewer_filename = os.path.basename(fbx_output_path)\n        else:\n            viewer_filename = fbx_output_path\n\n        return {\n            "ui": {\n                "fbx_file": [viewer_filename],\n                "bone_debug_data": [json.dumps(bone_debug_data)],\n            }\n        }\n\n\nclass UniRigDebugSkeleton:\n    """\n    Debug skeleton visualization with bone roll/orientation analysis.\n\n    Opens the FBX in an enhanced debug viewer with:\n    - RGB axes showing local bone coordinate systems (X=red, Y=green, Z=blue/roll)\n    - Bone name labels\n    - Detailed bone information panel with roll angles\n    - Animation playback controls\n    - Bone filtering and size controls\n    """\n\n    @classmethod\n    def INPUT_TYPES(cls):\n        return {\n            "required": {\n                "fbx_path": ("STRING", {\n                    "tooltip": "Path to FBX file (from output directory or absolute path)"\n                }),\n            },\n        }\n\n    RETURN_TYPES = ()\n    OUTPUT_NODE = True\n    FUNCTION = "debug_skeleton"\n    CATEGORY = "unirig"\n\n    def debug_skeleton(self, fbx_path):\n        """Open the FBX in the debug skeleton viewer."""\n        log.debug("Preparing debug skeleton view...")\n\n        # Handle both relative paths and absolute paths\n        output_dir = _get_output_directory()\n\n        if os.path.isabs(fbx_path):\n            full_path = fbx_path\n        else:\n            full_path = os.path.join(output_dir, fbx_path)\n\n        if not os.path.exists(full_path):\n            raise RuntimeError(f"FBX file not found: {fbx_path}")\n\n        log.debug("FBX path: %s", full_path)\n\n        # For the viewer, use relative path if in output, otherwise basename\n        if os.path.isabs(fbx_path):\n            viewer_filename = os.path.basename(fbx_path)\n        else:\n            viewer_filename = fbx_path\n\n        return {\n            "ui": {\n                "fbx_file": [viewer_filename],\n            }\n        }\n\n\nclass UniRigCompareSkeletons:\n    """\n    Compare two skeletons side-by-side with synced rotation.\n\n    Opens two FBX files in a split-view debug viewer where:\n    - Both skeletons are displayed side-by-side\n    - Camera rotation and zoom are synced between views\n    - Clicking a bone in one view highlights the matching bone (by name) in the other\n    """\n\n    @classmethod\n    def INPUT_TYPES(cls):\n        return {\n            "required": {\n                "fbx_path_left": ("STRING", {\n                    "tooltip": "Path to left skeleton FBX file (from output directory or absolute path)"\n                }),\n                "fbx_path_right": ("STRING", {\n                    "tooltip": "Path to right skeleton FBX file (from output directory or absolute path)"\n                }),\n            },\n        }\n\n    RETURN_TYPES = ()\n    OUTPUT_NODE = True\n    FUNCTION = "compare_skeletons"\n    CATEGORY = "unirig"\n\n    def compare_skeletons(self, fbx_path_left, fbx_path_right):\n        """Open both FBX files in the comparison skeleton viewer."""\n        log.info("Preparing skeleton comparison view...")\n\n        output_dir = _get_output_directory()\n\n        # Validate left FBX path\n        if os.path.isabs(fbx_path_left):\n            full_path_left = fbx_path_left\n        else:\n            full_path_left = os.path.join(output_dir, fbx_path_left)\n\n        if not os.path.exists(full_path_left):\n            raise RuntimeError(f"Left FBX file not found: {fbx_path_left}")\n\n        # Validate right FBX path\n        if os.path.isabs(fbx_path_right):\n            full_path_right = fbx_path_right\n        else:\n            full_path_right = os.path.join(output_dir, fbx_path_right)\n\n        if not os.path.exists(full_path_right):\n            raise RuntimeError(f"Right FBX file not found: {fbx_path_right}")\n\n        log.info("Left FBX: %s", full_path_left)\n        log.info("Right FBX: %s", full_path_right)\n\n        # For the viewer, use relative path if in output, otherwise basename\n        if os.path.isabs(fbx_path_left):\n            viewer_filename_left = os.path.basename(fbx_path_left)\n        else:\n            viewer_filename_left = fbx_path_left\n\n        if os.path.isabs(fbx_path_right):\n            viewer_filename_right = os.path.basename(fbx_path_right)\n        else:\n            viewer_filename_right = fbx_path_right\n\n        return {\n            "ui": {\n                "fbx_file_left": [viewer_filename_left],\n                "fbx_file_right": [viewer_filename_right],\n            }\n        }\n',
    'load_model.py': '"""\nModel loader nodes for UniRig.\n\nDownloads checkpoints, resolves precision/attention config.\nActual model loading happens lazily in inference nodes via direct.py.\n"""\n\nimport logging\nimport os\nimport sys\nfrom pathlib import Path\n\nimport torch\n\nlog = logging.getLogger("unirig")\n\n# Attention backend options\nATTN_BACKENDS = [\'auto\', \'flash_attn\', \'sdpa\']\n\n# Support both relative imports (ComfyUI) and absolute imports (testing)\ntry:\n    from .base import UNIRIG_PATH, UNIRIG_MODELS_DIR\nexcept ImportError:\n    from base import UNIRIG_PATH, UNIRIG_MODELS_DIR\n\n# Global config cache (for config dicts only, no model loading)\n_MODEL_CACHE = {}\n\n\nclass UniRigLoadSkeletonModel:\n    """\n    Load and cache the UniRig skeleton extraction model.\n\n    This pre-downloads the model weights and prepares configuration\n    for faster skeleton inference. Connect this to UniRigExtractSkeleton\n    to avoid model reload on each run.\n    """\n\n    @classmethod\n    def INPUT_TYPES(cls):\n        return {\n            "required": {\n                "model_id": ("STRING", {\n                    "default": "apozz/UniRig-safetensors",\n                    "tooltip": "HuggingFace model ID for skeleton model"\n                }),\n                "cache_to_gpu": ("BOOLEAN", {\n                    "default": True,\n                    "tooltip": "Keep model cached on GPU for faster inference. Disable to offload to CPU after inference (saves VRAM)."\n                }),\n            },\n        }\n\n    RETURN_TYPES = ("UNIRIG_SKELETON_MODEL",)\n    RETURN_NAMES = ("skeleton_model",)\n    FUNCTION = "load_model"\n    CATEGORY = "UniRig/Models"\n\n    def load_model(self, model_id="apozz/UniRig-safetensors", cache_to_gpu=True, **kwargs):\n        """Download and cache skeleton model configuration. No model loading."""\n        log.info("Loading skeleton model config: %s", model_id)\n\n        cache_key = f"skeleton_{model_id}"\n\n        # Check cache\n        if cache_key in _MODEL_CACHE:\n            cached_model = _MODEL_CACHE[cache_key]\n            log.info("Using cached model configuration")\n            return (cached_model,)\n\n        # Download checkpoint\n        try:\n            from .unirig.download import download\n            from .unirig.configs import SKELETON_CHECKPOINT\n\n            log.info("Downloading/verifying checkpoint...")\n            local_checkpoint = download(SKELETON_CHECKPOINT)\n            log.info("Checkpoint ready: %s", local_checkpoint)\n\n            model_wrapper = {\n                "type": "skeleton",\n                "model_id": model_id,\n                "checkpoint_path": local_checkpoint,\n                "unirig_path": UNIRIG_PATH,\n                "models_dir": str(UNIRIG_MODELS_DIR),\n            }\n\n            _MODEL_CACHE[cache_key] = model_wrapper\n            log.info("Skeleton model config cached (checkpoint: %s)", local_checkpoint)\n            return (model_wrapper,)\n\n        except Exception as e:\n            log.error("Error loading model: %s", e, exc_info=True)\n            model_wrapper = {\n                "type": "skeleton",\n                "model_id": model_id,\n                "unirig_path": UNIRIG_PATH,\n                "models_dir": str(UNIRIG_MODELS_DIR),\n            }\n            return (model_wrapper,)\n\n\nclass UniRigLoadSkinningModel:\n    """\n    Load and cache the UniRig skinning weight prediction model.\n\n    This pre-downloads the model weights and prepares configuration\n    for faster skinning inference. Connect this to UniRigApplySkinningML\n    to avoid model reload on each run.\n    """\n\n    @classmethod\n    def INPUT_TYPES(cls):\n        return {\n            "required": {\n                "model_id": ("STRING", {\n                    "default": "apozz/UniRig-safetensors",\n                    "tooltip": "HuggingFace model ID for skinning model"\n                }),\n                "cache_to_gpu": ("BOOLEAN", {\n                    "default": True,\n                    "tooltip": "Keep model cached on GPU for faster inference. Disable to offload to CPU after inference (saves VRAM)."\n                }),\n            },\n        }\n\n    RETURN_TYPES = ("UNIRIG_SKINNING_MODEL",)\n    RETURN_NAMES = ("skinning_model",)\n    FUNCTION = "load_model"\n    CATEGORY = "UniRig/Models"\n\n    def load_model(self, model_id="apozz/UniRig-safetensors", cache_to_gpu=True, **kwargs):\n        """Download and cache skinning model configuration. No model loading."""\n        log.info("Loading skinning model config: %s", model_id)\n\n        cache_key = f"skinning_{model_id}"\n\n        # Check cache\n        if cache_key in _MODEL_CACHE:\n            cached_model = _MODEL_CACHE[cache_key]\n            log.info("Using cached model configuration")\n            return (cached_model,)\n\n        # Download checkpoint\n        try:\n            from .unirig.download import download\n            from .unirig.configs import SKIN_CHECKPOINT\n\n            log.info("Downloading/verifying checkpoint...")\n            local_checkpoint = download(SKIN_CHECKPOINT)\n            log.info("Checkpoint ready: %s", local_checkpoint)\n\n            model_wrapper = {\n                "type": "skinning",\n                "model_id": model_id,\n                "checkpoint_path": local_checkpoint,\n                "unirig_path": UNIRIG_PATH,\n                "models_dir": str(UNIRIG_MODELS_DIR),\n            }\n\n            _MODEL_CACHE[cache_key] = model_wrapper\n            log.info("Skinning model config cached (checkpoint: %s)", local_checkpoint)\n            return (model_wrapper,)\n\n        except Exception as e:\n            log.error("Error loading model: %s", e, exc_info=True)\n            model_wrapper = {\n                "type": "skinning",\n                "model_id": model_id,\n                "unirig_path": UNIRIG_PATH,\n                "models_dir": str(UNIRIG_MODELS_DIR),\n            }\n            return (model_wrapper,)\n\n\nclass UniRigLoadModel:\n    """Load UniRig model configuration for the rigging pipeline.\n\n    Downloads checkpoints and resolves precision/attention settings.\n    Actual model loading happens lazily in inference nodes.\n    """\n\n    @classmethod\n    def INPUT_TYPES(cls):\n        return {\n            "required": {},\n            "optional": {\n                "precision": (["auto", "bf16", "fp16", "fp32"], {\n                    "default": "auto",\n                    "tooltip": "Model precision. auto: best for your GPU (bf16 on Ampere+, fp16 on Volta/Turing, fp32 on older)."\n                }),\n                "attn_backend": (ATTN_BACKENDS, {\n                    "default": "auto",\n                    "tooltip": "Attention backend. auto: best available (flash_attn > sdpa). flash_attn requires flash-attn package."\n                }),\n            },\n        }\n\n    RETURN_TYPES = ("UNIRIG_MODEL",)\n    RETURN_NAMES = ("model",)\n    FUNCTION = "load_models"\n    CATEGORY = "UniRig"\n\n    def load_models(self, precision="auto", attn_backend="auto", **kwargs):\n        """Download checkpoints and resolve precision/attention config."""\n        # UNIRIG_COMFY_PATH_BRIDGE_V1\n        # In ComfyUI Desktop Local, comfy-env worker may only receive the user\n        # directory on sys.path, not the real ComfyUI application root. Add the\n        # detected/known ComfyUI root before importing comfy.model_management.\n        comfy_root_candidates = []\n\n        env_root = os.environ.get("COMFYUI_PATH") or os.environ.get("COMFYUI_ROOT")\n        if env_root:\n            comfy_root_candidates.append(env_root)\n\n        # Desktop Local default observed path. Safe no-op if absent.\n        comfy_root_candidates.append(r"D:\\ComfyUI_Local\\resources\\ComfyUI")\n\n        # Also try walking upward from this custom node location.\n        here = Path(__file__).resolve()\n        for parent in here.parents:\n            if (parent / "comfy").is_dir():\n                comfy_root_candidates.append(str(parent))\n\n        for candidate in comfy_root_candidates:\n            if candidate and os.path.isdir(os.path.join(candidate, "comfy")) and candidate not in sys.path:\n                sys.path.insert(0, candidate)\n                log.info("Added ComfyUI root to sys.path for worker: %s", candidate)\n                break\n\n        import comfy.model_management as mm\n        # Resolve precision\n        device = mm.get_torch_device()\n        if precision == "auto":\n            if mm.should_use_bf16(device):\n                dtype = "bf16"\n            elif mm.should_use_fp16(device):\n                dtype = "fp16"\n            else:\n                dtype = "fp32"\n        else:\n            dtype = precision\n\n        log.info("Resolved precision: %s -> %s", precision, dtype)\n        log.info("Attention backend: %s", attn_backend)\n\n        model_id = "apozz/UniRig-safetensors"\n\n        # Download skeleton checkpoint\n        skeleton_loader = UniRigLoadSkeletonModel()\n        skeleton_result = skeleton_loader.load_model(model_id=model_id)\n        skeleton_model = skeleton_result[0]\n\n        # Download skinning checkpoint\n        skinning_loader = UniRigLoadSkinningModel()\n        skinning_result = skinning_loader.load_model(model_id=model_id)\n        skinning_model = skinning_result[0]\n\n        # Propagate dtype and attn_backend into sub-model dicts\n        # so inference nodes can access them directly\n        skeleton_model["dtype"] = dtype\n        skeleton_model["attn_backend"] = attn_backend\n        skinning_model["dtype"] = dtype\n        skinning_model["attn_backend"] = attn_backend\n\n        combined_model = {\n            "skeleton_model": skeleton_model,\n            "skinning_model": skinning_model,\n            "model_id": model_id,\n            "dtype": dtype,\n            "attn_backend": attn_backend,\n        }\n\n        log.info("UniRig model config ready")\n        return (combined_model,)\n\n\ndef clear_model_cache():\n    """Clear the global model cache (configs, loaded models, MIA models)."""\n    import comfy.model_management as mm\n    global _MODEL_CACHE\n    _MODEL_CACHE.clear()\n    mm.soft_empty_cache()\n    log.info("Model cache cleared")\n\n\ndef get_cached_models():\n    """Get list of cached model keys."""\n    return list(_MODEL_CACHE.keys())\n\n\nclass MIALoadModel:\n    """\n    Load Make-It-Animatable models for fast humanoid rigging.\n\n    Downloads models from HuggingFace on first use (~500MB total).\n    MIA is optimized for humanoid characters and outputs Mixamo-compatible skeletons.\n\n    Faster than UniRig (<1 second) but only supports humanoid characters with Mixamo skeleton.\n    """\n\n    @classmethod\n    def INPUT_TYPES(cls):\n        return {\n            "required": {},\n            "optional": {\n                "precision": (["auto", "bf16", "fp16", "fp32"], {\n                    "default": "auto",\n                    "tooltip": "Model precision. auto: best for your GPU (bf16 on Ampere+, fp16 on Volta/Turing, fp32 on older)."\n                }),\n                "attn_backend": (ATTN_BACKENDS, {\n                    "default": "auto",\n                    "tooltip": "Attention backend. auto: best available (flash_attn > sdpa). flash_attn requires flash-attn package."\n                }),\n            },\n        }\n\n    RETURN_TYPES = ("MIA_MODEL",)\n    RETURN_NAMES = ("model",)\n    FUNCTION = "load_models"\n    CATEGORY = "UniRig/MIA"\n\n    def load_models(self, precision="auto", attn_backend="auto"):\n        """Return MIA config with resolved precision."""\n        import comfy.model_management as mm\n        device = mm.get_torch_device()\n        if precision == "auto":\n            if mm.should_use_bf16(device):\n                dtype = "bf16"\n            elif mm.should_use_fp16(device):\n                dtype = "fp16"\n            else:\n                dtype = "fp32"\n        else:\n            dtype = precision\n\n        log.info("MIA config: precision=%s -> %s, attn_backend=%s", precision, dtype, attn_backend)\n        return ({\n            "backend": "mia",\n            "dtype": dtype,\n            "attn_backend": attn_backend,\n        },)\n',
    'direct_preprocess.py': '# UNIRIG_PREPROCESS_BPY_BRIDGE_V3_DLL_IMPORT\n"""\nDirect mesh preprocessing using bpy as a Python module.\n\nThis module provides the same functionality as blender_extract.py but as a\ndirect Python import, eliminating the need for subprocess calls to Blender.\n\nRequires: bpy>=4.0.0 (installed via pip install bpy)\n\nIMPORTANT: bpy is imported lazily inside functions to avoid\nconflicts with torch_cluster. Do NOT add module-level bpy imports.\n"""\n\nimport numpy as np\nfrom pathlib import Path\nimport base64\nimport struct\nimport zlib\nimport os\nimport sys\nimport subprocess\nimport glob\nimport logging\n\nlog = logging.getLogger("unirig")\n\n\ndef _add_env_dll_dirs_for_bpy():\n    """Make Blender/bpy DLLs visible when running from comfy-env/pixi on Windows."""\n    candidates = []\n    try:\n        py = Path(sys.executable).resolve()\n        candidates.extend([py.parent, py.parent / "Library" / "bin", py.parent / "Scripts", py.parent / "bin"])\n        for parent in py.parents:\n            candidates.extend([parent / "Library" / "bin", parent / "Scripts", parent / "bin"])\n    except Exception:\n        pass\n    hinted = os.environ.get("UNIRIG_ENV_PYTHON") or os.environ.get("UNIRIG_DIRECT_ENV_PYTHON")\n    if hinted:\n        try:\n            hp = Path(hinted).resolve()\n            for parent in [hp.parent] + list(hp.parents):\n                candidates.extend([parent / "Library" / "bin", parent / "Scripts", parent / "bin"])\n        except Exception:\n            pass\n    added = []\n    for candidate in candidates:\n        try:\n            if candidate.exists() and candidate.is_dir():\n                c = str(candidate)\n                if c not in added:\n                    added.append(c)\n                    if hasattr(os, "add_dll_directory"):\n                        try:\n                            os.add_dll_directory(c)\n                        except Exception:\n                            pass\n        except Exception:\n            pass\n    if added:\n        current_path = os.environ.get("PATH", "")\n        prefix = os.pathsep.join(added)\n        os.environ["PATH"] = prefix + os.pathsep + current_path if current_path else prefix\n\n\ndef _find_unirig_env_python() -> str:\n    """Find the Python executable inside UniRig\'s isolated comfy-env environment."""\n    nodes_dir = Path(__file__).resolve().parent.parent\n    candidates = []\n\n    # Preferred: the local _env_* entry inside nodes/ (normally a junction).\n    for env_dir in sorted(nodes_dir.glob("_env_*"), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True):\n        py = env_dir / "python.exe"\n        if py.exists():\n            candidates.append(py)\n        py = env_dir / ".pixi" / "envs" / "default" / "python.exe"\n        if py.exists():\n            candidates.append(py)\n\n    # Fallback: global comfy-env caches.\n    for root in (Path("C:/ce"), Path("D:/ce"), Path("E:/ce")):\n        if root.exists():\n            for env_dir in sorted(root.glob("_env_*"), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True):\n                py = env_dir / ".pixi" / "envs" / "default" / "python.exe"\n                if py.exists():\n                    candidates.append(py)\n                py = env_dir / "python.exe"\n                if py.exists():\n                    candidates.append(py)\n\n    if not candidates:\n        raise FileNotFoundError(\n            "Unable to find UniRig isolated environment python.exe. "\n            "Expected nodes\\\\_env_*\\\\python.exe or C:\\\\ce/D:\\\\ce/E:\\\\ce\\\\_env_*\\\\.pixi\\\\envs\\\\default\\\\python.exe."\n        )\n\n    return str(candidates[0])\n\n\ndef _run_preprocess_in_unirig_env(input_file: str, output_npz: str, target_face_count: int) -> dict:\n    """Run this same module in UniRig\'s isolated env where bpy is installed."""\n    env_python = _find_unirig_env_python()\n    env = os.environ.copy()\n    env["UNIRIG_BPY_BRIDGE_CHILD"] = "1"\n    env["UNIRIG_ENV_PYTHON"] = env_python\n\n    cmd = [\n        env_python,\n        str(Path(__file__).resolve()),\n        "--child-preprocess",\n        input_file,\n        output_npz,\n        str(int(target_face_count)),\n    ]\n\n    # Put env DLL locations first for bpy/Blender DLL resolution.\n    try:\n        py = Path(env_python).resolve()\n        dll_candidates = [py.parent, py.parent / "Library" / "bin", py.parent / "Scripts", py.parent / "bin"]\n        for parent in py.parents:\n            dll_candidates.extend([parent / "Library" / "bin", parent / "Scripts", parent / "bin"])\n        path_prefix = []\n        for c in dll_candidates:\n            try:\n                if c.exists() and c.is_dir():\n                    value = str(c)\n                    if value not in path_prefix:\n                        path_prefix.append(value)\n            except Exception:\n                pass\n        if path_prefix:\n            env["PATH"] = os.pathsep.join(path_prefix) + os.pathsep + env.get("PATH", "")\n    except Exception:\n        pass\n\n    log.info("bpy not available in ComfyUI Python; running preprocessing in UniRig env: %s", env_python)\n    completed = subprocess.run(cmd, env=env, text=True, capture_output=True)\n\n    if completed.stdout:\n        for line in completed.stdout.splitlines():\n            log.info("[bpy-env] %s", line)\n    if completed.stderr:\n        for line in completed.stderr.splitlines():\n            log.warning("[bpy-env] %s", line)\n\n    if completed.returncode != 0:\n        raise RuntimeError(\n            f"UniRig bpy bridge failed with exit code {completed.returncode}. "\n            f"Command: {\' \'.join(cmd)}"\n        )\n\n    if not os.path.exists(output_npz):\n        raise FileNotFoundError(f"UniRig bpy bridge completed but output was not created: {output_npz}")\n\n    data = np.load(output_npz, allow_pickle=True)\n    return {key: data[key] for key in data.files}\n\n\ndef preprocess_mesh(\n    input_file: str,\n    output_npz: str,\n    target_face_count: int = 50000\n) -> dict:\n    """\n    Preprocess mesh for UniRig inference.\n\n    Does:\n    - Import mesh (OBJ, FBX, GLB, DAE, STL)\n    - Join multiple meshes\n    - Apply transforms\n    - Triangulate\n    - Decimate to target face count\n    - Extract vertices, faces, normals\n    - Extract UV coordinates\n    - Extract texture data\n    - Save to NPZ\n\n    Args:\n        input_file: Path to input mesh file\n        output_npz: Path to output NPZ file\n        target_face_count: Target number of faces after decimation\n\n    Returns:\n        dict with mesh data (vertices, faces, normals, etc.)\n    """\n    # Lazy import to avoid torch_cluster conflict.\n    # If ComfyUI\'s main Python cannot import bpy, delegate only this preprocessing\n    # step to UniRig\'s isolated comfy-env Python, where bpy is installed.\n    try:\n        _add_env_dll_dirs_for_bpy()\n        import bpy\n    except Exception:\n        if os.environ.get("UNIRIG_BPY_BRIDGE_CHILD") == "1":\n            raise\n        return _run_preprocess_in_unirig_env(input_file, output_npz, target_face_count)\n\n    log.info("Input: %s", input_file)\n    log.info("Output: %s", output_npz)\n    log.info("Target faces: %s", target_face_count)\n\n    # Clear scene\n    bpy.ops.object.select_all(action=\'SELECT\')\n    bpy.ops.object.delete()\n\n    # Import mesh based on file extension\n    ext = Path(input_file).suffix.lower()\n    log.info("Loading %s file...", ext)\n\n    try:\n        if ext == \'.obj\':\n            bpy.ops.wm.obj_import(filepath=input_file)\n        elif ext in [\'.fbx\', \'.FBX\']:\n            bpy.ops.import_scene.fbx(filepath=input_file, ignore_leaf_bones=False, use_image_search=False)\n        elif ext in [\'.glb\', \'.gltf\']:\n            bpy.ops.import_scene.gltf(filepath=input_file, import_pack_images=False)\n        elif ext == \'.dae\':\n            bpy.ops.wm.collada_import(filepath=input_file)\n        elif ext == \'.stl\':\n            bpy.ops.wm.stl_import(filepath=input_file)\n        else:\n            raise ValueError(f"Unsupported format: {ext}")\n\n        log.info("Import successful")\n\n    except Exception as e:\n        log.info("Import failed: %s", e)\n        raise\n\n    # Get all meshes\n    meshes = [obj for obj in bpy.context.scene.objects if obj.type == \'MESH\']\n\n    if not meshes:\n        raise RuntimeError("No meshes found in file")\n\n    log.info(f"Found {len(meshes)} mesh(es)")\n\n    # Combine all meshes\n    if len(meshes) > 1:\n        # Select all meshes\n        bpy.ops.object.select_all(action=\'DESELECT\')\n        for obj in meshes:\n            obj.select_set(True)\n        bpy.context.view_layer.objects.active = meshes[0]\n\n        # Join meshes\n        bpy.ops.object.join()\n        mesh_obj = bpy.context.active_object\n    else:\n        mesh_obj = meshes[0]\n\n    log.info("Processing mesh: %s", mesh_obj.name)\n\n    # Apply all transforms\n    bpy.ops.object.select_all(action=\'DESELECT\')\n    mesh_obj.select_set(True)\n    bpy.context.view_layer.objects.active = mesh_obj\n    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)\n\n    # Get mesh data\n    mesh = mesh_obj.data\n\n    # Triangulate\n    log.info("Triangulating...")\n    bpy.ops.object.mode_set(mode=\'EDIT\')\n    bpy.ops.mesh.select_all(action=\'SELECT\')\n    bpy.ops.mesh.quads_convert_to_tris()\n    bpy.ops.object.mode_set(mode=\'OBJECT\')\n\n    # Simplify if needed\n    current_faces = len(mesh.polygons)\n    log.info("Current face count: %s", current_faces)\n\n    if current_faces > target_face_count:\n        log.info("Decimating to %s faces...", target_face_count)\n\n        # Add decimate modifier\n        decimate_mod = mesh_obj.modifiers.new(name=\'Decimate\', type=\'DECIMATE\')\n        decimate_mod.ratio = target_face_count / current_faces\n        decimate_mod.use_collapse_triangulate = True\n\n        # Apply modifier\n        bpy.ops.object.modifier_apply(modifier=decimate_mod.name)\n\n        log.info(f"Decimated to {len(mesh.polygons)} faces")\n\n    # Extract vertex and face data\n    vertices = np.zeros((len(mesh.vertices), 3), dtype=np.float32)\n    for i, v in enumerate(mesh.vertices):\n        vertices[i] = v.co\n\n    faces = np.zeros((len(mesh.polygons), 3), dtype=np.int32)\n    for i, p in enumerate(mesh.polygons):\n        if len(p.vertices) != 3:\n            log.warning("Warning: Non-triangular face found")\n            continue\n        faces[i] = [p.vertices[0], p.vertices[1], p.vertices[2]]\n\n    log.info(f"Extracted {len(vertices)} vertices, {len(faces)} faces")\n\n    # Calculate vertex normals (Blender 4.2+ compatible)\n    # Force recalculation by updating the mesh\n    bpy.ops.object.mode_set(mode=\'EDIT\')\n    bpy.ops.object.mode_set(mode=\'OBJECT\')\n\n    vertex_normals = np.zeros((len(vertices), 3), dtype=np.float32)\n    for i, v in enumerate(mesh.vertices):\n        vertex_normals[i] = v.normal\n\n    log.info("Calculated vertex normals")\n\n    # Calculate face normals\n    face_normals = np.zeros((len(faces), 3), dtype=np.float32)\n    for i, p in enumerate(mesh.polygons):\n        face_normals[i] = p.normal\n\n    log.info("Calculated face normals")\n\n    # Extract UV coordinates if available\n    uv_coords = None\n    uv_faces = None\n    if mesh.uv_layers.active:\n        uv_layer = mesh.uv_layers.active.data\n        # UV coordinates are stored per loop (face corner), not per vertex\n        # We need to map them to face corners\n        uv_coords_list = []\n        uv_faces_list = []\n\n        for i, poly in enumerate(mesh.polygons):\n            face_uvs = []\n            for loop_idx in poly.loop_indices:\n                uv = uv_layer[loop_idx].uv\n                uv_coords_list.append([uv[0], uv[1]])\n                face_uvs.append(len(uv_coords_list) - 1)\n            uv_faces_list.append(face_uvs)\n\n        uv_coords = np.array(uv_coords_list, dtype=np.float32)\n        uv_faces = np.array(uv_faces_list, dtype=np.int32)\n        log.info(f"Extracted UV coordinates: {len(uv_coords)} UVs for {len(uv_faces)} faces")\n    else:\n        log.info("No UV layer found")\n\n    # Extract material/texture info if available\n    material_name = None\n    texture_path = None\n    texture_data_base64 = ""\n    texture_format = ""\n    texture_width = 0\n    texture_height = 0\n\n    if mesh_obj.material_slots:\n        mat = mesh_obj.material_slots[0].material\n        if mat:\n            material_name = mat.name\n            # Try to find base color texture\n            if mat.use_nodes:\n                for node in mat.node_tree.nodes:\n                    if node.type == \'TEX_IMAGE\' and node.image:\n                        texture_path = node.image.filepath\n                        log.info("Found texture node: %s", node.name)\n                        log.info("Texture path: %s", texture_path)\n\n                        # Extract actual image data\n                        tex_base64, tex_fmt, tex_w, tex_h = _extract_texture_from_image(node.image)\n                        if tex_base64:\n                            texture_data_base64 = tex_base64\n                            texture_format = tex_fmt\n                            texture_width = tex_w\n                            texture_height = tex_h\n                            log.info("Texture extracted successfully: %sx%s %s", tex_w, tex_h, tex_fmt)\n                        break\n            log.info("Material: %s", material_name)\n\n    # Save as NPZ (raw_data format expected by UniRig)\n    # For skeleton extraction, skeleton fields are set to None\n    os.makedirs(os.path.dirname(output_npz), exist_ok=True)\n\n    np.savez_compressed(\n        output_npz,\n        vertices=vertices.astype(np.float32),\n        vertex_normals=vertex_normals.astype(np.float32),\n        faces=faces.astype(np.int32),\n        face_normals=face_normals.astype(np.float32),\n        uv_coords=uv_coords if uv_coords is not None else np.array([], dtype=np.float32),\n        uv_faces=uv_faces if uv_faces is not None else np.array([], dtype=np.int32),\n        material_name=material_name if material_name else "",\n        texture_path=texture_path if texture_path else "",\n        texture_data_base64=texture_data_base64,\n        texture_format=texture_format,\n        texture_width=texture_width,\n        texture_height=texture_height,\n        joints=None,\n        skin=None,\n        parents=None,\n        names=None,\n        matrix_local=None,\n    )\n\n    log.info("Saved to: %s", output_npz)\n    if texture_data_base64:\n        log.info("Texture data included: %sx%s %s", texture_width, texture_height, texture_format)\n    else:\n        log.info("No texture data extracted")\n    log.info("Done!")\n\n    # Return mesh data dict for convenience\n    return {\n        \'vertices\': vertices,\n        \'vertex_normals\': vertex_normals,\n        \'faces\': faces,\n        \'face_normals\': face_normals,\n        \'uv_coords\': uv_coords,\n        \'uv_faces\': uv_faces,\n        \'material_name\': material_name,\n        \'texture_path\': texture_path,\n        \'texture_data_base64\': texture_data_base64,\n        \'texture_format\': texture_format,\n        \'texture_width\': texture_width,\n        \'texture_height\': texture_height,\n    }\n\n\ndef _extract_texture_from_image(image, max_size=2048):\n    """Extract texture data from Blender image as base64 encoded PNG string.\n    Uses pure Python PNG encoding without PIL dependency."""\n\n    try:\n        # Get image dimensions\n        width, height = image.size\n        channels = image.channels\n\n        log.info("Extracting texture: %sx%s, %s channels", width, height, channels)\n\n        # Get pixel data - Blender stores as flat RGBA float array\n        pixels = np.array(image.pixels[:])\n\n        # Reshape to (height, width, channels)\n        pixels = pixels.reshape((height, width, channels))\n\n        # Convert from float [0,1] to uint8 [0,255]\n        pixels = (np.clip(pixels, 0, 1) * 255).astype(np.uint8)\n\n        # Flip vertically (Blender stores bottom-to-top)\n        pixels = np.flipud(pixels)\n\n        # Resize if too large (simple nearest-neighbor downsampling)\n        if width > max_size or height > max_size:\n            scale = max_size / max(width, height)\n            new_width = int(width * scale)\n            new_height = int(height * scale)\n            log.info("Resizing texture from %sx%s to %sx%s", width, height, new_width, new_height)\n\n            # Simple nearest-neighbor resize using numpy\n            row_indices = (np.arange(new_height) * height / new_height).astype(int)\n            col_indices = (np.arange(new_width) * width / new_width).astype(int)\n            pixels = pixels[row_indices][:, col_indices]\n            width, height = new_width, new_height\n\n        # Encode as PNG without PIL - use pure Python PNG encoder\n        png_data = _encode_png(pixels, width, height, channels)\n\n        # Encode to base64\n        encoded = base64.b64encode(png_data).decode(\'utf-8\')\n\n        log.info(f"Texture encoded: {len(encoded) / 1024:.1f} KB base64")\n        return encoded, \'PNG\', width, height\n\n    except Exception as e:\n        log.error("Failed to extract texture from mesh", exc_info=True)\n        return None, None, 0, 0\n\n\ndef _encode_png(pixels, width, height, channels):\n    """\n    Encode numpy pixel array to PNG format without PIL.\n    Uses minimal PNG implementation with zlib compression.\n    """\n\n    def png_chunk(chunk_type, data):\n        """Create a PNG chunk with CRC."""\n        chunk_len = struct.pack(\'>I\', len(data))\n        chunk_data = chunk_type + data\n        checksum = struct.pack(\'>I\', zlib.crc32(chunk_data) & 0xffffffff)\n        return chunk_len + chunk_data + checksum\n\n    # PNG signature\n    signature = b\'\\x89PNG\\r\\n\\x1a\\n\'\n\n    # IHDR chunk (image header)\n    if channels == 4:\n        color_type = 6  # RGBA\n    elif channels == 3:\n        color_type = 2  # RGB\n    else:\n        # Convert to RGB\n        if channels == 1:\n            pixels = np.repeat(pixels, 3, axis=2)\n            channels = 3\n            color_type = 2\n        else:\n            raise ValueError(f"Unsupported channel count: {channels}")\n\n    bit_depth = 8\n    compression = 0\n    filter_method = 0\n    interlace = 0\n\n    ihdr_data = struct.pack(\'>IIBBBBB\', width, height, bit_depth, color_type,\n                            compression, filter_method, interlace)\n    ihdr_chunk = png_chunk(b\'IHDR\', ihdr_data)\n\n    # IDAT chunk (compressed image data)\n    # Prepare raw data with filter bytes\n    raw_data = b\'\'\n    for row in pixels:\n        # Filter type 0 (None) for each row\n        raw_data += b\'\\x00\'\n        raw_data += row.tobytes()\n\n    # Compress with zlib\n    compressed = zlib.compress(raw_data, level=6)\n    idat_chunk = png_chunk(b\'IDAT\', compressed)\n\n    # IEND chunk (end of image)\n    iend_chunk = png_chunk(b\'IEND\', b\'\')\n\n    # Combine all chunks\n    png_data = signature + ihdr_chunk + idat_chunk + iend_chunk\n\n    return png_data\n\n\nif __name__ == "__main__":\n    if len(sys.argv) == 5 and sys.argv[1] == "--child-preprocess":\n        preprocess_mesh(sys.argv[2], sys.argv[3], int(sys.argv[4]))\n    else:\n        print("Usage: python direct_preprocess.py --child-preprocess <input_file> <output_npz> <target_face_count>")\n        sys.exit(2)\n',
    'direct_export_fbx.py': '# UNIRIG_EXPORT_BPY_BRIDGE_V3_DLL_IMPORT\n"""\nDirect FBX export using bpy as a Python module.\n\nThis module provides the same functionality as blender_export_fbx.py but as a\ndirect Python import, eliminating the need for subprocess calls to Blender.\n\nRequires: bpy>=4.0.0 (installed via pip install bpy)\n\nIMPORTANT: bpy and mathutils are imported lazily inside functions to avoid\nconflicts with torch_cluster. Do NOT add module-level bpy imports.\n"""\n\nimport numpy as np\nfrom collections import defaultdict\nimport math\nimport tempfile\nimport base64\nimport os\nimport sys\nimport subprocess\nimport pickle\nimport logging\nfrom pathlib import Path\n\nlog = logging.getLogger("unirig")\n\n\n# UNIRIG_EXPORT_BPY_BRIDGE_V1\ndef _add_env_dll_dirs_for_bpy():\n    """Make Blender/bpy DLLs visible when running from comfy-env/pixi on Windows."""\n    candidates = []\n    try:\n        py = Path(sys.executable).resolve()\n        # ...\\_env_xxx\\.pixi\\envs\\default\\python.exe\n        env_root = py.parent\n        candidates.extend([\n            env_root,\n            env_root / "Library" / "bin",\n            env_root / "Scripts",\n            env_root / "bin",\n        ])\n        # also climb parents, useful when sys.executable is inside .pixi\\envs\\default\n        for parent in py.parents:\n            candidates.extend([\n                parent / "Library" / "bin",\n                parent / "Scripts",\n                parent / "bin",\n            ])\n    except Exception:\n        pass\n\n    # Extra hint from parent process, if provided.\n    hinted = os.environ.get("UNIRIG_ENV_PYTHON") or os.environ.get("UNIRIG_DIRECT_ENV_PYTHON")\n    if hinted:\n        try:\n            hp = Path(hinted).resolve()\n            for parent in [hp.parent] + list(hp.parents):\n                candidates.extend([\n                    parent / "Library" / "bin",\n                    parent / "Scripts",\n                    parent / "bin",\n                ])\n        except Exception:\n            pass\n\n    added = []\n    for candidate in candidates:\n        try:\n            if candidate.exists() and candidate.is_dir():\n                c = str(candidate)\n                if c not in added:\n                    added.append(c)\n                    if hasattr(os, "add_dll_directory"):\n                        try:\n                            os.add_dll_directory(c)\n                        except Exception:\n                            pass\n        except Exception:\n            pass\n\n    if added:\n        current_path = os.environ.get("PATH", "")\n        prefix = os.pathsep.join(added)\n        os.environ["PATH"] = prefix + os.pathsep + current_path if current_path else prefix\n\n\ndef _find_env_python_for_export() -> str:\n    """Find UniRig isolated env Python from nodes/_env_* junction."""\n    nodes_dir = Path(__file__).resolve().parents[1]  # ...\\nodes\n    candidates = []\n    for env_dir in sorted(nodes_dir.glob("_env_*"), reverse=True):\n        candidates.extend([\n            env_dir / ".pixi" / "envs" / "default" / "python.exe",\n            env_dir / "python.exe",\n        ])\n        try:\n            resolved = env_dir.resolve(strict=True)\n            candidates.extend([\n                resolved / ".pixi" / "envs" / "default" / "python.exe",\n                resolved / "python.exe",\n            ])\n        except Exception:\n            pass\n    for candidate in candidates:\n        if candidate.exists():\n            return str(candidate)\n    return ""\n\n\ndef _run_export_subprocess(payload: dict) -> str:\n    env_python = _find_env_python_for_export()\n    if not env_python:\n        raise RuntimeError("UniRig env python not found for FBX export bpy bridge")\n\n    with tempfile.TemporaryDirectory(prefix="unirig_export_bpy_") as td:\n        in_file = Path(td) / "payload.pkl"\n        out_file = Path(td) / "result.pkl"\n        with open(in_file, "wb") as f:\n            pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)\n\n        env = os.environ.copy()\n        env["UNIRIG_EXPORT_BPY_CHILD"] = "1"\n        env["UNIRIG_ENV_PYTHON"] = env_python\n\n        # Put env DLL locations first for bpy/Blender DLL resolution.\n        py = Path(env_python).resolve()\n        dll_candidates = [\n            py.parent,\n            py.parent / "Library" / "bin",\n            py.parent / "Scripts",\n            py.parent / "bin",\n        ]\n        for parent in py.parents:\n            dll_candidates.extend([parent / "Library" / "bin", parent / "Scripts", parent / "bin"])\n        path_prefix = []\n        for c in dll_candidates:\n            try:\n                if c.exists() and c.is_dir():\n                    s = str(c)\n                    if s not in path_prefix:\n                        path_prefix.append(s)\n            except Exception:\n                pass\n        if path_prefix:\n            env["PATH"] = os.pathsep.join(path_prefix) + os.pathsep + env.get("PATH", "")\n\n        cmd = [\n            env_python,\n            str(Path(__file__).resolve()),\n            "--unirig-export-bpy-subprocess",\n            str(in_file),\n            str(out_file),\n        ]\n\n        result = subprocess.run(\n            cmd,\n            capture_output=True,\n            text=True,\n            encoding="utf-8",\n            errors="replace",\n            env=env,\n            check=False,\n        )\n\n        if result.stdout:\n            for line in result.stdout.splitlines():\n                log.info("[export-bpy-subprocess] %s", line)\n        if result.stderr:\n            for line in result.stderr.splitlines():\n                log.info("[export-bpy-subprocess][stderr] %s", line)\n\n        if result.returncode != 0:\n            raise RuntimeError(f"FBX export bpy subprocess failed with exit code {result.returncode}")\n        if not out_file.exists():\n            raise RuntimeError("FBX export subprocess completed but result file was not created")\n\n        with open(out_file, "rb") as f:\n            data = pickle.load(f)\n        if not data.get("ok"):\n            raise RuntimeError(data.get("error") or "FBX export subprocess failed")\n        return data["output_fbx"]\n\n\ndef export_rigged_fbx(*args, **kwargs) -> str:\n    """\n    Bridge wrapper for FBX export.\n\n    First tries normal in-process export after adding DLL paths.\n    If bpy DLL loading fails, delegates the export to UniRig isolated env Python.\n    """\n    _add_env_dll_dirs_for_bpy()\n\n    try:\n        return _export_rigged_fbx_impl(*args, **kwargs)\n    except Exception as exc:\n        # Only bridge bpy/DLL import failures; re-raise normal export errors.\n        message = str(exc)\n        is_bpy_error = (\n            "bpy" in message.lower()\n            or "dll load failed" in message.lower()\n            or exc.__class__.__name__ in {"ImportError", "ModuleNotFoundError", "OSError"}\n        )\n        if os.environ.get("UNIRIG_EXPORT_BPY_CHILD") == "1" or not is_bpy_error:\n            raise\n\n        log.info("FBX export bpy failed in current process, switching to UniRig env subprocess: %s", exc)\n        return _run_export_subprocess({"args": args, "kwargs": kwargs})\n\n\ndef _cli_main() -> int:\n    if len(sys.argv) >= 4 and sys.argv[1] == "--unirig-export-bpy-subprocess":\n        _add_env_dll_dirs_for_bpy()\n        in_file = Path(sys.argv[2])\n        out_file = Path(sys.argv[3])\n        try:\n            with open(in_file, "rb") as f:\n                payload = pickle.load(f)\n            output_fbx = _export_rigged_fbx_impl(*payload.get("args", ()), **payload.get("kwargs", {}))\n            with open(out_file, "wb") as f:\n                pickle.dump({"ok": True, "output_fbx": output_fbx}, f, protocol=pickle.HIGHEST_PROTOCOL)\n            return 0\n        except Exception as exc:\n            import traceback\n            with open(out_file, "wb") as f:\n                pickle.dump({"ok": False, "error": str(exc), "traceback": traceback.format_exc()}, f, protocol=pickle.HIGHEST_PROTOCOL)\n            traceback.print_exc()\n            return 1\n    return 0\n\n\ndef _export_rigged_fbx_impl(\n    joints: np.ndarray,\n    parents: list,\n    names: list,\n    output_fbx: str,\n    vertices: np.ndarray = None,\n    faces: np.ndarray = None,\n    skin: np.ndarray = None,\n    tails: np.ndarray = None,\n    uv_coords: np.ndarray = None,\n    uv_faces: np.ndarray = None,\n    texture_data_base64: str = "",\n    texture_format: str = "PNG",\n    material_name: str = "Material",\n    extrude_size: float = 0.03,\n    add_root: bool = False,\n    use_extrude_bone: bool = True,\n    use_connect_unique_child: bool = True,\n    extrude_from_parent: bool = True,\n) -> str:\n    """\n    Export skeleton and optionally skinned mesh to FBX format.\n\n    Args:\n        joints: Joint positions array (N, 3)\n        parents: Parent indices list (N,) - None or -1 for root\n        names: Bone names list (N,)\n        output_fbx: Output FBX file path\n        vertices: Optional mesh vertices (V, 3)\n        faces: Optional mesh faces (F, 3)\n        skin: Optional skin weights (V, N)\n        tails: Optional bone tail positions (N, 3)\n        uv_coords: Optional UV coordinates\n        uv_faces: Optional UV face indices\n        texture_data_base64: Optional base64 encoded texture\n        texture_format: Texture format (default: PNG)\n        material_name: Material name\n        extrude_size: Default bone extrusion size\n        add_root: Whether to add a root bone\n        use_extrude_bone: Whether to extrude bones\n        use_connect_unique_child: Whether to connect unique children\n        extrude_from_parent: Whether to extrude from parent direction\n\n    Returns:\n        Path to the exported FBX file\n    """\n    # Lazy imports to avoid torch_cluster conflict\n    import bpy\n    from mathutils import Vector, Matrix, Quaternion\n\n    log.info("Input joints: %s", joints.shape)\n    log.info("Output: %s", output_fbx)\n\n    # Convert inputs to numpy arrays\n    joints = np.array(joints, dtype=np.float32)\n    if tails is not None:\n        tails = np.array(tails, dtype=np.float32)\n    if vertices is not None:\n        vertices = np.array(vertices, dtype=np.float32)\n    if faces is not None:\n        faces = np.array(faces, dtype=np.int32)\n    if skin is not None:\n        skin = np.array(skin, dtype=np.float32)\n    if uv_coords is not None and len(uv_coords) > 0:\n        uv_coords = np.array(uv_coords, dtype=np.float32)\n    else:\n        uv_coords = None\n    if uv_faces is not None and len(uv_faces) > 0:\n        uv_faces = np.array(uv_faces, dtype=np.int32)\n    else:\n        uv_faces = None\n\n    if texture_data_base64 and len(texture_data_base64) > 0:\n        log.info(f"Found texture data: {texture_format} ({len(texture_data_base64) // 1024}KB base64)")\n    else:\n        log.info("No texture data found")\n\n    log.info(f"Loaded skeleton with {len(joints)} joints")\n    if vertices is not None:\n        log.info(f"Found mesh with {len(vertices)} vertices")\n    if skin is not None:\n        log.info("Skin weights shape: %s", skin.shape)\n\n    # Clean default scene\n    _clean_bpy()\n\n    # === T-POSE CONVERSION FOR SMPL SKELETONS ===\n    SMPL_JOINT_NAMES_CHECK = [\'Pelvis\', \'L_Hip\', \'R_Hip\', \'Spine1\', \'L_Knee\', \'R_Knee\',\n                        \'Spine2\', \'L_Ankle\', \'R_Ankle\', \'Spine3\', \'L_Foot\', \'R_Foot\',\n                        \'Neck\', \'L_Collar\', \'R_Collar\', \'Head\', \'L_Shoulder\', \'R_Shoulder\',\n                        \'L_Elbow\', \'R_Elbow\', \'L_Wrist\', \'R_Wrist\']\n\n    is_smpl_skeleton = len(names) == 22 and all(n in SMPL_JOINT_NAMES_CHECK for n in names)\n\n    if is_smpl_skeleton:\n        joints, tails, vertices = _convert_smpl_tpose(joints, tails, vertices, skin, names)\n\n    # === MIXAMO NORMALIZATION ===\n    is_mixamo_skeleton = any(n.startswith(\'mixamorig:\') for n in names)\n\n    if is_mixamo_skeleton and vertices is not None and skin is not None:\n        joints, tails, vertices = _normalize_mixamo(joints, tails, vertices, skin, names)\n\n    # Make collection\n    collection = bpy.data.collections.new(\'new_collection\')\n    bpy.context.scene.collection.children.link(collection)\n\n    # Make mesh if vertices provided\n    if vertices is not None:\n        mesh = bpy.data.meshes.new(\'mesh\')\n        if faces is None:\n            faces = []\n        mesh.from_pydata(vertices.tolist(), [], faces.tolist() if isinstance(faces, np.ndarray) else [])\n        mesh.update()\n\n        # Add UV coordinates if available\n        if uv_coords is not None and uv_faces is not None and len(uv_coords) > 0:\n            log.info(f"Adding UV coordinates: {len(uv_coords)} UVs")\n            uv_layer = mesh.uv_layers.new(name=\'UVMap\')\n\n            for face_idx, poly in enumerate(mesh.polygons):\n                if face_idx < len(uv_faces):\n                    for loop_offset, loop_idx in enumerate(poly.loop_indices):\n                        uv_idx = uv_faces[face_idx][loop_offset]\n                        if uv_idx < len(uv_coords):\n                            uv_layer.data[loop_idx].uv = uv_coords[uv_idx]\n\n            log.info("UV coordinates applied")\n\n        # Make object from mesh\n        obj = bpy.data.objects.new(\'character\', mesh)\n        collection.objects.link(obj)\n\n        # Create and apply textured material if texture data is available\n        if texture_data_base64 and len(texture_data_base64) > 0:\n            _apply_texture(obj, texture_data_base64, material_name)\n\n    # Create armature\n    log.info("Creating armature...")\n    bpy.ops.object.armature_add(enter_editmode=True)\n    armature = bpy.data.armatures.get(\'Armature\')\n    edit_bones = armature.edit_bones\n\n    J = joints.shape[0]\n    if tails is None:\n        log.info("Tails not provided, auto-generating...")\n        tails = joints.copy()\n        tails[:, 2] += extrude_size\n\n    connects = [False for _ in range(J)]\n    children = defaultdict(list)\n    for i in range(1, J):\n        if parents[i] is not None and parents[i] != -1:\n            children[parents[i]].append(i)\n\n    if tails is not None:\n        if use_extrude_bone:\n            for i in range(J):\n                if len(children[i]) != 1 and extrude_from_parent and i != 0:\n                    if parents[i] is not None and parents[i] != -1:\n                        pjoint = joints[parents[i]]\n                        joint = joints[i]\n                        d = joint - pjoint\n                        if np.linalg.norm(d) < 0.000001:\n                            d = np.array([0., 0., 1.])\n                        else:\n                            d = d / np.linalg.norm(d)\n                        tails[i] = joint + d * extrude_size\n        if use_connect_unique_child:\n            for i in range(J):\n                if len(children[i]) == 1:\n                    child = children[i][0]\n                    tails[i] = joints[child]\n                if parents[i] is not None and parents[i] != -1 and len(children[parents[i]]) == 1:\n                    connects[i] = True\n\n    # Create root bone\n    if add_root:\n        bone_root = edit_bones.get(\'Bone\')\n        bone_root.name = \'Root\'\n        bone_root.tail = Vector((joints[0, 0], joints[0, 1], joints[0, 2]))\n    else:\n        bone_root = edit_bones.get(\'Bone\')\n        bone_root.name = names[0]\n        bone_root.head = Vector((joints[0, 0], joints[0, 1], joints[0, 2]))\n        bone_root.tail = Vector((joints[0, 0], joints[0, 1], joints[0, 2] + extrude_size))\n\n    # Create bones\n    for i in range(J):\n        if add_root is False and i == 0:\n            continue\n        edit_bones = armature.edit_bones\n        pname = \'Root\' if parents[i] is None or parents[i] == -1 else names[parents[i]]\n        _extrude_bone(edit_bones, names[i], pname, joints[i], tails[i], connects[i])\n\n    # Update bone positions\n    for i in range(J):\n        bone = edit_bones.get(names[i])\n        bone.head = Vector((joints[i, 0], joints[i, 1], joints[i, 2]))\n        bone.tail = Vector((tails[i, 0], tails[i, 1], tails[i, 2]))\n\n    # Fix bone orientations for Mixamo\n    if is_mixamo_skeleton:\n        _fix_mixamo_bone_orientations(edit_bones, names)\n\n    # Set bone rolls for SMPL\n    if is_smpl_skeleton:\n        _set_smpl_bone_rolls(edit_bones, names, J)\n\n    # Add skinning weights\n    if vertices is not None and skin is not None:\n        log.info("Adding skinning weights...")\n        bpy.ops.object.mode_set(mode=\'OBJECT\')\n        objects = bpy.data.objects\n        for o in bpy.context.selected_objects:\n            o.select_set(False)\n        ob = objects[\'character\']\n        arm = bpy.data.objects[\'Armature\']\n        ob.select_set(True)\n        arm.select_set(True)\n        bpy.ops.object.parent_set(type=\'ARMATURE_NAME\')\n\n        vis = [x.name for x in ob.vertex_groups]\n\n        # Sparsify\n        argsorted = np.argsort(-skin, axis=1)\n        vertex_group_reweight = skin[np.arange(skin.shape[0])[..., None], argsorted]\n\n        group_per_vertex = vertex_group_reweight.shape[-1]\n        vertex_group_reweight = vertex_group_reweight / vertex_group_reweight[..., :group_per_vertex].sum(axis=1)[..., None]\n\n        for v, w in enumerate(skin):\n            for ii in range(group_per_vertex):\n                i = argsorted[v, ii]\n                if i >= J:\n                    continue\n                n = names[i]\n                if n not in vis:\n                    continue\n                ob.vertex_groups[n].add([v], vertex_group_reweight[v, ii], \'REPLACE\')\n\n    log.info("Armature created successfully")\n\n    # Apply Mixamo-standard object transforms\n    if is_mixamo_skeleton:\n        log.info("Applying Mixamo-standard object transforms...")\n        bpy.ops.object.mode_set(mode=\'OBJECT\')\n\n        arm_obj = bpy.data.objects.get(\'Armature\')\n        if arm_obj:\n            arm_obj.rotation_euler = (math.radians(90), 0, 0)\n            arm_obj.scale = (0.01, 0.01, 0.01)\n\n        bpy.context.view_layer.update()\n\n    # Export to FBX\n    log.info("Exporting to FBX...")\n    os.makedirs(os.path.dirname(output_fbx) if os.path.dirname(output_fbx) else \'.\', exist_ok=True)\n\n    bpy.ops.export_scene.fbx(\n        filepath=output_fbx,\n        check_existing=False,\n        add_leaf_bones=False,\n        path_mode=\'COPY\',\n        embed_textures=True,\n    )\n    log.info("Saved to: %s", output_fbx)\n    log.info("Done!")\n\n    return output_fbx\n\n\ndef _clean_bpy():\n    """Clean the Blender scene."""\n    import bpy  # Lazy import\n\n    for c in bpy.data.actions:\n        bpy.data.actions.remove(c)\n    for c in bpy.data.armatures:\n        bpy.data.armatures.remove(c)\n    for c in bpy.data.cameras:\n        bpy.data.cameras.remove(c)\n    for c in bpy.data.collections:\n        bpy.data.collections.remove(c)\n    for c in bpy.data.images:\n        bpy.data.images.remove(c)\n    for c in bpy.data.materials:\n        bpy.data.materials.remove(c)\n    for c in bpy.data.meshes:\n        bpy.data.meshes.remove(c)\n    for c in bpy.data.objects:\n        bpy.data.objects.remove(c)\n    for c in bpy.data.textures:\n        bpy.data.textures.remove(c)\n\n\ndef _extrude_bone(edit_bones, name, parent_name, head, tail, connect):\n    """Create a new bone."""\n    from mathutils import Vector  # Lazy import\n\n    bone = edit_bones.new(name)\n    bone.head = Vector((head[0], head[1], head[2]))\n    bone.tail = Vector((tail[0], tail[1], tail[2]))\n    bone.name = name\n    parent_bone = edit_bones.get(parent_name)\n    bone.parent = parent_bone\n    bone.use_connect = connect\n\n\ndef _convert_smpl_tpose(joints, tails, vertices, skin, names):\n    """Convert SMPL skeleton to T-pose if needed."""\n    log.info("Detected SMPL skeleton, checking T-pose...")\n\n    l_shoulder_idx = names.index(\'L_Shoulder\')\n    l_elbow_idx = names.index(\'L_Elbow\')\n    l_wrist_idx = names.index(\'L_Wrist\')\n    r_shoulder_idx = names.index(\'R_Shoulder\')\n    r_elbow_idx = names.index(\'R_Elbow\')\n    r_wrist_idx = names.index(\'R_Wrist\')\n\n    l_shoulder = joints[l_shoulder_idx]\n    l_elbow = joints[l_elbow_idx]\n    l_wrist = joints[l_wrist_idx]\n    r_shoulder = joints[r_shoulder_idx]\n    r_elbow = joints[r_elbow_idx]\n    r_wrist = joints[r_wrist_idx]\n\n    # Detect lateral axis\n    shoulder_diff = r_shoulder - l_shoulder\n    if abs(shoulder_diff[0]) > abs(shoulder_diff[2]):\n        l_tpose_dir = np.array([1.0, 0.0, 0.0])\n        r_tpose_dir = np.array([-1.0, 0.0, 0.0])\n    else:\n        if l_shoulder[2] < r_shoulder[2]:\n            l_tpose_dir = np.array([0.0, 0.0, -1.0])\n            r_tpose_dir = np.array([0.0, 0.0, 1.0])\n        else:\n            l_tpose_dir = np.array([0.0, 0.0, 1.0])\n            r_tpose_dir = np.array([0.0, 0.0, -1.0])\n\n    # Check if already T-posed\n    l_arm_vec = l_wrist - l_shoulder\n    l_arm_vec_norm = l_arm_vec / (np.linalg.norm(l_arm_vec) + 1e-8)\n\n    if abs(l_arm_vec_norm[1]) < 0.1:\n        log.info("Arms already horizontal (T-pose)")\n        return joints, tails, vertices\n\n    log.info("Converting to T-pose...")\n\n    # Compute arm lengths\n    l_upper_len = np.linalg.norm(l_elbow - l_shoulder)\n    l_lower_len = np.linalg.norm(l_wrist - l_elbow)\n    r_upper_len = np.linalg.norm(r_elbow - r_shoulder)\n    r_lower_len = np.linalg.norm(r_wrist - r_elbow)\n\n    # New T-pose positions\n    new_l_elbow = l_shoulder + l_tpose_dir * l_upper_len\n    new_l_wrist = new_l_elbow + l_tpose_dir * l_lower_len\n    new_r_elbow = r_shoulder + r_tpose_dir * r_upper_len\n    new_r_wrist = new_r_elbow + r_tpose_dir * r_lower_len\n\n    # Compute rotations\n    l_arm_vec_v = Vector(l_arm_vec).normalized()\n    new_l_arm_vec = Vector(new_l_wrist - l_shoulder).normalized()\n    l_rotation = l_arm_vec_v.rotation_difference(new_l_arm_vec)\n\n    r_arm_vec = r_wrist - r_shoulder\n    r_arm_vec_v = Vector(r_arm_vec).normalized()\n    new_r_arm_vec = Vector(new_r_wrist - r_shoulder).normalized()\n    r_rotation = r_arm_vec_v.rotation_difference(new_r_arm_vec)\n\n    # Transform vertices\n    if vertices is not None and skin is not None:\n        left_arm_bones = {\'L_Shoulder\', \'L_Elbow\', \'L_Wrist\'}\n        right_arm_bones = {\'R_Shoulder\', \'R_Elbow\', \'R_Wrist\'}\n\n        left_bone_indices = [names.index(b) for b in left_arm_bones if b in names]\n        right_bone_indices = [names.index(b) for b in right_arm_bones if b in names]\n\n        for v_idx in range(len(vertices)):\n            left_weight = sum(skin[v_idx, idx] for idx in left_bone_indices)\n            right_weight = sum(skin[v_idx, idx] for idx in right_bone_indices)\n\n            if left_weight < 0.001 and right_weight < 0.001:\n                continue\n\n            displacement = np.zeros(3)\n\n            if left_weight > 0.001:\n                rel_pos = vertices[v_idx] - l_shoulder\n                rotated = np.array(l_rotation @ Vector(rel_pos))\n                displacement += (rotated - rel_pos) * left_weight\n\n            if right_weight > 0.001:\n                rel_pos = vertices[v_idx] - r_shoulder\n                rotated = np.array(r_rotation @ Vector(rel_pos))\n                displacement += (rotated - rel_pos) * right_weight\n\n            vertices[v_idx] += displacement\n\n    # Update joints\n    joints[l_elbow_idx] = new_l_elbow\n    joints[l_wrist_idx] = new_l_wrist\n    joints[r_elbow_idx] = new_r_elbow\n    joints[r_wrist_idx] = new_r_wrist\n\n    # Update tails\n    if tails is not None:\n        tails[l_shoulder_idx] = new_l_elbow\n        tails[r_shoulder_idx] = new_r_elbow\n        tails[l_elbow_idx] = new_l_wrist\n        tails[r_elbow_idx] = new_r_wrist\n        wrist_tail_len = 0.05\n        tails[l_wrist_idx] = new_l_wrist + l_tpose_dir * wrist_tail_len\n        tails[r_wrist_idx] = new_r_wrist + r_tpose_dir * wrist_tail_len\n\n    log.info("T-pose conversion complete")\n    return joints, tails, vertices\n\n\ndef _normalize_mixamo(joints, tails, vertices, skin, names):\n    """Normalize Mixamo skeleton for animation compatibility."""\n    from mathutils import Vector, Quaternion\n    log.info("Normalizing Mixamo skeleton...")\n\n    # Get key bone indices\n    hips_idx = None\n    head_idx = None\n    l_arm_idx = None\n    r_arm_idx = None\n    l_forearm_idx = None\n    r_forearm_idx = None\n    l_hand_idx = None\n    r_hand_idx = None\n\n    for i, name in enumerate(names):\n        if name == \'mixamorig:Hips\':\n            hips_idx = i\n        elif name == \'mixamorig:Head\':\n            head_idx = i\n        elif name == \'mixamorig:LeftArm\':\n            l_arm_idx = i\n        elif name == \'mixamorig:RightArm\':\n            r_arm_idx = i\n        elif name == \'mixamorig:LeftForeArm\':\n            l_forearm_idx = i\n        elif name == \'mixamorig:RightForeArm\':\n            r_forearm_idx = i\n        elif name == \'mixamorig:LeftHand\':\n            l_hand_idx = i\n        elif name == \'mixamorig:RightHand\':\n            r_hand_idx = i\n\n    # Orient model to Mixamo standard\n    if l_arm_idx is not None and r_arm_idx is not None and hips_idx is not None:\n        l_shoulder = joints[l_arm_idx]\n        r_shoulder = joints[r_arm_idx]\n        hips = joints[hips_idx]\n        head = joints[head_idx] if head_idx is not None else joints[np.argmax(joints[:, 2])]\n\n        lateral_vec = r_shoulder - l_shoulder\n        lateral_vec = lateral_vec / (np.linalg.norm(lateral_vec) + 1e-8)\n\n        up_vec = head - hips\n        up_vec = up_vec / (np.linalg.norm(up_vec) + 1e-8)\n\n        lateral_xy = np.array([lateral_vec[0], lateral_vec[1], 0])\n        lateral_xy_len = np.linalg.norm(lateral_xy)\n\n        if lateral_xy_len > 0.1:\n            lateral_xy = lateral_xy / lateral_xy_len\n            target_lateral_xy = np.array([-1.0, 0.0])\n\n            dot = lateral_xy[0] * target_lateral_xy[0] + lateral_xy[1] * target_lateral_xy[1]\n            cross_z = lateral_xy[0] * target_lateral_xy[1] - lateral_xy[1] * target_lateral_xy[0]\n            z_rotation_angle = math.atan2(cross_z, dot)\n\n            if abs(z_rotation_angle) > 0.05:\n                cos_a = math.cos(z_rotation_angle)\n                sin_a = math.sin(z_rotation_angle)\n\n                def rotate_z(points):\n                    rotated = np.zeros_like(points)\n                    rotated[..., 0] = cos_a * points[..., 0] - sin_a * points[..., 1]\n                    rotated[..., 1] = sin_a * points[..., 0] + cos_a * points[..., 1]\n                    rotated[..., 2] = points[..., 2]\n                    return rotated\n\n                vertices = rotate_z(vertices)\n                joints = rotate_z(joints)\n                if tails is not None:\n                    tails = rotate_z(tails)\n\n    # T-pose conversion for Mixamo\n    if l_arm_idx is not None and r_arm_idx is not None and l_hand_idx is not None and r_hand_idx is not None:\n        l_shoulder = joints[l_arm_idx]\n        r_shoulder = joints[r_arm_idx]\n        l_hand = joints[l_hand_idx]\n        r_hand = joints[r_hand_idx]\n\n        l_tpose_dir = np.array([1.0, 0.0, 0.0])\n        r_tpose_dir = np.array([-1.0, 0.0, 0.0])\n\n        l_arm_vec = l_hand - l_shoulder\n        l_arm_vec_norm = l_arm_vec / (np.linalg.norm(l_arm_vec) + 1e-8)\n        l_arm_x_component = abs(l_arm_vec_norm[0])\n\n        if l_arm_x_component < 0.9:\n            # Need T-pose conversion - simplified version\n            l_elbow = joints[l_forearm_idx] if l_forearm_idx else None\n            r_elbow = joints[r_forearm_idx] if r_forearm_idx else None\n\n            if l_elbow is not None:\n                l_upper_len = np.linalg.norm(l_elbow - l_shoulder)\n                l_lower_len = np.linalg.norm(l_hand - l_elbow)\n            else:\n                l_upper_len = np.linalg.norm(l_hand - l_shoulder) / 2\n                l_lower_len = l_upper_len\n\n            if r_elbow is not None:\n                r_upper_len = np.linalg.norm(r_elbow - r_shoulder)\n                r_lower_len = np.linalg.norm(r_hand - r_elbow)\n            else:\n                r_upper_len = np.linalg.norm(r_hand - r_shoulder) / 2\n                r_lower_len = r_upper_len\n\n            new_l_elbow = l_shoulder + l_tpose_dir * l_upper_len if l_elbow is not None else None\n            new_l_hand = (new_l_elbow if new_l_elbow is not None else l_shoulder) + l_tpose_dir * l_lower_len\n            new_r_elbow = r_shoulder + r_tpose_dir * r_upper_len if r_elbow is not None else None\n            new_r_hand = (new_r_elbow if new_r_elbow is not None else r_shoulder) + r_tpose_dir * r_lower_len\n\n            # Compute rotations\n            l_arm_vec_v = Vector(l_arm_vec).normalized()\n            new_l_arm_vec = Vector(new_l_hand - l_shoulder).normalized()\n\n            l_rot_axis = l_arm_vec_v.cross(new_l_arm_vec)\n            if l_rot_axis.length > 0.0001:\n                l_rot_axis.normalize()\n                l_rot_angle = math.acos(max(-1, min(1, l_arm_vec_v.dot(new_l_arm_vec))))\n                l_rotation = Quaternion(l_rot_axis, l_rot_angle)\n            else:\n                l_rotation = Quaternion()\n\n            r_arm_vec = r_hand - r_shoulder\n            r_arm_vec_v = Vector(r_arm_vec).normalized()\n            new_r_arm_vec = Vector(new_r_hand - r_shoulder).normalized()\n\n            r_rot_axis = r_arm_vec_v.cross(new_r_arm_vec)\n            if r_rot_axis.length > 0.0001:\n                r_rot_axis.normalize()\n                r_rot_angle = math.acos(max(-1, min(1, r_arm_vec_v.dot(new_r_arm_vec))))\n                r_rotation = Quaternion(r_rot_axis, r_rot_angle)\n            else:\n                r_rotation = Quaternion()\n\n            # Transform vertices\n            left_arm_bones = {\'mixamorig:LeftArm\', \'mixamorig:LeftForeArm\', \'mixamorig:LeftHand\'}\n            right_arm_bones = {\'mixamorig:RightArm\', \'mixamorig:RightForeArm\', \'mixamorig:RightHand\'}\n\n            for name in names:\n                if name.startswith(\'mixamorig:LeftHand\'):\n                    left_arm_bones.add(name)\n                elif name.startswith(\'mixamorig:RightHand\'):\n                    right_arm_bones.add(name)\n\n            left_bone_indices = [names.index(b) for b in left_arm_bones if b in names]\n            right_bone_indices = [names.index(b) for b in right_arm_bones if b in names]\n\n            for v_idx in range(len(vertices)):\n                left_weight = sum(skin[v_idx, idx] for idx in left_bone_indices if idx < skin.shape[1])\n                right_weight = sum(skin[v_idx, idx] for idx in right_bone_indices if idx < skin.shape[1])\n\n                if left_weight < 0.001 and right_weight < 0.001:\n                    continue\n\n                displacement = np.zeros(3)\n\n                if left_weight > 0.001:\n                    rel_pos = vertices[v_idx] - l_shoulder\n                    rotated = np.array(l_rotation @ Vector(rel_pos))\n                    displacement += (rotated - rel_pos) * left_weight\n\n                if right_weight > 0.001:\n                    rel_pos = vertices[v_idx] - r_shoulder\n                    rotated = np.array(r_rotation @ Vector(rel_pos))\n                    displacement += (rotated - rel_pos) * right_weight\n\n                vertices[v_idx] += displacement\n\n            # Update joints\n            if l_forearm_idx is not None and new_l_elbow is not None:\n                joints[l_forearm_idx] = new_l_elbow\n            joints[l_hand_idx] = new_l_hand\n\n            if r_forearm_idx is not None and new_r_elbow is not None:\n                joints[r_forearm_idx] = new_r_elbow\n            joints[r_hand_idx] = new_r_hand\n\n            # Update tails\n            if tails is not None:\n                if l_forearm_idx is not None and new_l_elbow is not None:\n                    tails[l_arm_idx] = new_l_elbow\n                    tails[l_forearm_idx] = new_l_hand\n                else:\n                    tails[l_arm_idx] = new_l_hand\n\n                if r_forearm_idx is not None and new_r_elbow is not None:\n                    tails[r_arm_idx] = new_r_elbow\n                    tails[r_forearm_idx] = new_r_hand\n                else:\n                    tails[r_arm_idx] = new_r_hand\n\n                hand_tail_len = 0.05\n                tails[l_hand_idx] = new_l_hand + l_tpose_dir * hand_tail_len\n                tails[r_hand_idx] = new_r_hand + r_tpose_dir * hand_tail_len\n\n    # Scale to human size\n    current_height = vertices[:, 2].max() - vertices[:, 2].min()\n    target_height = 1.7\n\n    if current_height > 0.01:\n        scale_factor = target_height / current_height\n        vertices *= scale_factor\n        joints *= scale_factor\n        if tails is not None:\n            tails *= scale_factor\n\n    # Position feet at ground\n    mesh_min_z = vertices[:, 2].min()\n    z_offset = -mesh_min_z\n\n    vertices[:, 2] += z_offset\n    joints[:, 2] += z_offset\n    if tails is not None:\n        tails[:, 2] += z_offset\n\n    # Convert to Y-up\n    def convert_to_yup(coords):\n        result = np.zeros_like(coords)\n        result[..., 0] = coords[..., 0]\n        result[..., 1] = coords[..., 2]\n        result[..., 2] = -coords[..., 1]\n        return result\n\n    vertices = convert_to_yup(vertices) * 100.0\n    joints = convert_to_yup(joints) * 100.0\n    if tails is not None:\n        tails = convert_to_yup(tails) * 100.0\n\n    log.info("Mixamo normalization complete")\n    return joints, tails, vertices\n\n\ndef _apply_texture(obj, texture_data_base64, material_name):\n    """Apply texture to mesh object."""\n    import bpy  # Lazy import\n\n    log.info("Creating textured material...")\n    try:\n        # Ensure material_name is not None\n        if material_name is None:\n            material_name = "Material"\n\n        png_data = base64.b64decode(texture_data_base64)\n\n        with tempfile.NamedTemporaryFile(suffix=\'.png\', delete=False) as tmp:\n            tmp.write(png_data)\n            tmp_texture_path = tmp.name\n\n        mat = bpy.data.materials.new(name=material_name)\n        mat.use_nodes = True\n        mat.blend_method = \'OPAQUE\'\n        mat.shadow_method = \'OPAQUE\'\n\n        mat.node_tree.nodes.clear()\n\n        nodes = mat.node_tree.nodes\n        links = mat.node_tree.links\n\n        img_node = nodes.new(type=\'ShaderNodeTexImage\')\n        img_node.location = (-300, 300)\n\n        bsdf_node = nodes.new(type=\'ShaderNodeBsdfPrincipled\')\n        bsdf_node.location = (0, 300)\n        bsdf_node.inputs[\'Metallic\'].default_value = 0.0\n        bsdf_node.inputs[\'Roughness\'].default_value = 0.8\n        bsdf_node.inputs[\'Specular IOR Level\'].default_value = 0.3\n        bsdf_node.inputs[\'Alpha\'].default_value = 1.0\n\n        output_node = nodes.new(type=\'ShaderNodeOutputMaterial\')\n        output_node.location = (300, 300)\n\n        links.new(img_node.outputs[\'Color\'], bsdf_node.inputs[\'Base Color\'])\n        links.new(bsdf_node.outputs[\'BSDF\'], output_node.inputs[\'Surface\'])\n\n        blender_image = bpy.data.images.load(tmp_texture_path)\n        img_node.image = blender_image\n        blender_image.pack()\n\n        obj.data.materials.append(mat)\n\n        for poly in obj.data.polygons:\n            poly.material_index = 0\n\n        log.info("Textured material applied")\n\n        try:\n            os.remove(tmp_texture_path)\n        except:\n            pass\n\n    except Exception as tex_err:\n        log.warning("Warning: Could not apply texture: %s", tex_err)\n\n\ndef _fix_mixamo_bone_orientations(edit_bones, names):\n    """Fix bone orientations for Mixamo compatibility."""\n    from mathutils import Vector  # Lazy import\n\n    log.info("Fixing bone orientations for Mixamo...")\n\n    DEFAULT_BONE_LENGTH = 5.0\n\n    MIXAMO_BONE_DIRECTIONS = {\n        \'mixamorig:Hips\': Vector((0, 1, 0)),\n        \'mixamorig:Spine\': Vector((0, 1, 0)),\n        \'mixamorig:Spine1\': Vector((0, 1, 0)),\n        \'mixamorig:Spine2\': Vector((0, 1, 0)),\n        \'mixamorig:Neck\': Vector((0, 1, 0)),\n        \'mixamorig:Head\': Vector((0, 1, 0)),\n        \'mixamorig:LeftUpLeg\': Vector((0, -1, 0)),\n        \'mixamorig:LeftLeg\': Vector((0, -1, 0)),\n        \'mixamorig:LeftFoot\': Vector((0, -0.632, 0.775)).normalized(),\n        \'mixamorig:LeftToeBase\': Vector((0, -0.632, 0.775)).normalized(),\n        \'mixamorig:RightUpLeg\': Vector((0, -1, 0)),\n        \'mixamorig:RightLeg\': Vector((0, -1, 0)),\n        \'mixamorig:RightFoot\': Vector((0, -0.632, 0.775)).normalized(),\n        \'mixamorig:RightToeBase\': Vector((0, -0.632, 0.775)).normalized(),\n        \'mixamorig:LeftShoulder\': Vector((1, 0, 0)),\n        \'mixamorig:LeftArm\': Vector((1, 0, 0)),\n        \'mixamorig:LeftForeArm\': Vector((1, 0, 0)),\n        \'mixamorig:LeftHand\': Vector((1, 0, 0)),\n        \'mixamorig:RightShoulder\': Vector((-1, 0, 0)),\n        \'mixamorig:RightArm\': Vector((-1, 0, 0)),\n        \'mixamorig:RightForeArm\': Vector((-1, 0, 0)),\n        \'mixamorig:RightHand\': Vector((-1, 0, 0)),\n    }\n\n    for bone_name, target_direction in MIXAMO_BONE_DIRECTIONS.items():\n        bone = edit_bones.get(bone_name)\n        if not bone:\n            continue\n\n        current_direction = (bone.tail - bone.head).normalized()\n        dot = current_direction.dot(target_direction)\n\n        if dot < 0.95:\n            bone_length = (bone.tail - bone.head).length\n            if bone_length < 0.1:\n                bone_length = DEFAULT_BONE_LENGTH\n            bone.tail = bone.head + target_direction * bone_length\n\n    # Fix bone rolls\n    MIXAMO_BONE_ROLLS = {\n        \'mixamorig:LeftShoulder\': Vector((0, -1, 0)),\n        \'mixamorig:LeftArm\': Vector((0, -1, 0)),\n        \'mixamorig:LeftForeArm\': Vector((0, -1, 0)),\n        \'mixamorig:LeftHand\': Vector((0, -1, 0)),\n        \'mixamorig:RightShoulder\': Vector((0, -1, 0)),\n        \'mixamorig:RightArm\': Vector((0, -1, 0)),\n        \'mixamorig:RightForeArm\': Vector((0, -1, 0)),\n        \'mixamorig:RightHand\': Vector((0, -1, 0)),\n        \'mixamorig:LeftUpLeg\': Vector((0, 0, 1)),\n        \'mixamorig:LeftLeg\': Vector((0, 0, 1)),\n        \'mixamorig:LeftFoot\': Vector((0, 1, 0)),\n        \'mixamorig:LeftToeBase\': Vector((0, 1, 0)),\n        \'mixamorig:RightUpLeg\': Vector((0, 0, 1)),\n        \'mixamorig:RightLeg\': Vector((0, 0, 1)),\n        \'mixamorig:RightFoot\': Vector((0, 1, 0)),\n        \'mixamorig:RightToeBase\': Vector((0, 1, 0)),\n        \'mixamorig:Hips\': Vector((0, 0, 1)),\n        \'mixamorig:Spine\': Vector((0, 0, 1)),\n        \'mixamorig:Spine1\': Vector((0, 0, 1)),\n        \'mixamorig:Spine2\': Vector((0, 0, 1)),\n        \'mixamorig:Neck\': Vector((0, 0, 1)),\n        \'mixamorig:Head\': Vector((0, 0, 1)),\n    }\n\n    for bone_name, target_z in MIXAMO_BONE_ROLLS.items():\n        bone = edit_bones.get(bone_name)\n        if bone:\n            bone.align_roll(target_z)\n\n\ndef _set_smpl_bone_rolls(edit_bones, names, J):\n    """Set bone rolls for SMPL compatibility."""\n    log.info("Setting bone rolls for SMPL...")\n\n    for i in range(J):\n        bone = edit_bones.get(names[i])\n        if bone:\n            direction = (bone.tail - bone.head).normalized()\n            dx, dy, dz = direction.x, direction.y, direction.z\n\n            if abs(dx) > 0.9:\n                bone.align_roll(Vector((0, 1, 0)))\n            elif abs(dy) > 0.9:\n                bone.align_roll(Vector((0, 0, 1)))\n            elif abs(dz) > 0.9:\n                bone.align_roll(Vector((0, 1, 0)))\n            else:\n                bone.align_roll(Vector((0, 1, 0)))\n\n\nif __name__ == "__main__":\n    raise SystemExit(_cli_main())\n',
}

PATCH_TARGETS = [
    {"name": "auto_rig env runner full path", "relative": Path("nodes") / "auto_rig.py", "template": "auto_rig.py", "markers": ["UNIRIG_AUTO_RIG_ENV_RUNNER_V4_FULL_PATH"]},
    {"name": "mesh_io manual path + fallback", "relative": Path("nodes") / "mesh_io.py", "template": "mesh_io.py", "markers": ["UNIRIG_MESH_IO_MANUAL_PATH_V2", "Manual mesh path"]},
    {"name": "base folder_paths safe", "relative": Path("nodes") / "base.py", "template": "base.py", "markers": ["UNIRIG_BASE_FOLDER_PATHS_SAFE_V1", "folder_paths"]},
    {"name": "skeleton_extraction folder_paths safe", "relative": Path("nodes") / "skeleton_extraction.py", "template": "skeleton_extraction.py", "markers": ["UNIRIG_FOLDER_PATHS_SAFE_SKELETON_V1"]},
    {"name": "skinning safe output unique", "relative": Path("nodes") / "skinning.py", "template": "skinning.py", "markers": ["UNIRIG_SKINNING_FOLDER_PATHS_SAFE_UNIQUE_OUTPUT_V2", "_next_fbx_filename"]},
    {"name": "skeleton_io preview copy", "relative": Path("nodes") / "skeleton_io.py", "template": "skeleton_io.py", "markers": ["UNIRIG_SKELETON_IO_PREVIEW_COPY_V2", "_safe_preview_filename"]},
    {"name": "load_model comfy path bridge", "relative": Path("nodes") / "load_model.py", "template": "load_model.py", "markers": ["UNIRIG_COMFY_PATH_BRIDGE_V1"]},
    {"name": "direct_preprocess bpy bridge", "relative": Path("nodes") / "unirig" / "direct_preprocess.py", "template": "direct_preprocess.py", "markers": ["UNIRIG_PREPROCESS_BPY_BRIDGE_V3_DLL_IMPORT", "UNIRIG_BPY_BRIDGE_CHILD", "_add_env_dll_dirs_for_bpy"]},
    {"name": "direct_export_fbx bpy bridge", "relative": Path("nodes") / "unirig" / "direct_export_fbx.py", "template": "direct_export_fbx.py", "markers": ["UNIRIG_EXPORT_BPY_BRIDGE_V3_DLL_IMPORT", "UNIRIG_EXPORT_BPY_CHILD", "_add_env_dll_dirs_for_bpy"]},
]

def _patch_backup_path(target: Path) -> Path:
    return target.with_name(target.name + ".unirig_official_backup")


def _is_patch_applied(target: Path, markers) -> bool:
    if not target.exists():
        return False
    try:
        content = target.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False
    return all(marker in content for marker in markers)


def _write_patch_file(target: Path, content: str, log, label: str):
    target.parent.mkdir(parents=True, exist_ok=True)
    backup = _patch_backup_path(target)
    if target.exists() and not backup.exists():
        shutil.copy2(target, backup)
        log(f"Backup created for {label}: {backup.name}")
    target.write_text(content, encoding="utf-8", newline="\n")
    log(f"Patch written: {label}")


def apply_safe_unirig_patches(unirig_path: str, log):
    """Apply the validated UniRig patches safely and idempotently."""
    root = Path(unirig_path)
    if not root.exists():
        raise RuntimeError(f"UniRig path not found for patching: {root}")
    applied = 0
    skipped = 0
    log("=== SAFE PATCH MODULE ===")
    for spec in PATCH_TARGETS:
        target = root / spec["relative"]
        label = spec["name"]
        template = PATCH_TEMPLATES[spec["template"]]
        markers = spec["markers"]
        if _is_patch_applied(target, markers):
            log(f"Patch already locked: {label}")
            skipped += 1
            continue
        if not target.exists():
            raise RuntimeError(f"Patch target missing: {target}")
        _write_patch_file(target, template, log, label)
        if not _is_patch_applied(target, markers):
            raise RuntimeError(f"Patch verification failed: {label}")
        log(f"Patch verified: {label}")
        applied += 1
    log(f"Safe patch summary: applied={applied}, already_ok={skipped}")
    return True


def validate_safe_unirig_patches(unirig_path: str, log):
    root = Path(unirig_path)
    missing = []
    for spec in PATCH_TARGETS:
        target = root / spec["relative"]
        if not _is_patch_applied(target, spec["markers"]):
            missing.append(spec["name"])
    if missing:
        log("Patch validation missing: " + ", ".join(missing))
        return False, missing
    log("Patch validation: OK")
    return True, []

class CommandExecutionError(RuntimeError):
    def __init__(self, cmd, exit_code, output_lines):
        self.cmd = list(cmd)
        self.exit_code = exit_code
        self.output_lines = list(output_lines)
        super().__init__(f"Command failed with exit code {exit_code}")


def run_stream(cmd, cwd=None, log=None):
    if log:
        log("$ " + " ".join(map(str, cmd)))
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert process.stdout is not None
    output_lines = []
    for line in process.stdout:
        line = line.rstrip()
        if line:
            output_lines.append(line)
            if log:
                log(line)
    code = process.wait()
    if code != 0:
        raise CommandExecutionError(cmd, code, output_lines)
    return output_lines


def get_target_comfy_env_version(env_mode: str) -> str:
    return COMFY_ENV_VERSION


def extract_install_paths(output_lines):
    build_dir = ""
    env_path = ""
    for line in output_lines or []:
        if "[comfy-env] build_dir=" in line:
            build_dir = line.split("[comfy-env] build_dir=", 1)[1].strip()
        elif "[comfy-env] env_path=" in line:
            env_path = line.split("[comfy-env] env_path=", 1)[1].strip()
    return {"build_dir": build_dir, "env_path": env_path}


def candidate_env_python_paths(base_path: str):
    if not base_path:
        return []
    base = Path(base_path)
    if base.name.lower() == "python.exe":
        return [base]
    return [
        base / "python.exe",
        base / ".pixi" / "envs" / "default" / "python.exe",
        base / ".pixi" / "envs" / "default" / "Scripts" / "python.exe",
    ]


def resolve_env_python_from_paths(paths):
    seen = set()
    for raw in paths:
        if not raw:
            continue
        for candidate in candidate_env_python_paths(raw):
            key = str(candidate).lower()
            if key in seen:
                continue
            seen.add(key)
            if candidate.exists():
                return str(candidate)
        try:
            resolved = str(Path(raw).resolve(strict=True))
        except Exception:
            resolved = ""
        if resolved:
            for candidate in candidate_env_python_paths(resolved):
                key = str(candidate).lower()
                if key in seen:
                    continue
                seen.add(key)
                if candidate.exists():
                    return str(candidate)
    return ""





def _is_reparse_point(path: Path) -> bool:
    """Best-effort test for Windows symlink/junction/reparse point."""
    try:
        if path.is_symlink():
            return True
        if os.name == "nt" and (path.exists() or path.is_symlink()):
            st = os.stat(path, follow_symlinks=False)
            attrs = getattr(st, "st_file_attributes", 0)
            return bool(attrs & 0x400)  # FILE_ATTRIBUTE_REPARSE_POINT
    except Exception:
        pass
    return False


def _remove_path_for_relink(path: Path, log):
    if not path.exists() and not path.is_symlink():
        return

    # On Windows, directory symlinks/junctions must be removed with rmdir,
    # not shutil.rmtree(), otherwise Python raises:
    # "Cannot call rmtree on a symbolic link".
    if _is_reparse_point(path):
        if os.name == "nt":
            result = subprocess.run(
                ["cmd", "/c", "rmdir", str(path)],
                capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
            )
            if result.returncode != 0 and result.stderr:
                log(result.stderr.strip())
        else:
            try:
                path.unlink()
            except IsADirectoryError:
                os.rmdir(path)
        if path.exists() or path.is_symlink():
            try:
                path.unlink()
            except Exception:
                pass
    elif path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    if path.exists() or path.is_symlink():
        raise RuntimeError(f"Unable to remove existing env path before relink: {path}")


def ensure_runtime_env_link(env_path: str, build_dir: str, log):
    """Publish comfy-env build_dir as nodes\\_env_xxx using a Windows junction.

    Safe/idempotent behavior:
    - existing correct junction: keep it
    - existing normal folder at nodes\\_env_xxx: replace it with junction
    - missing target: create junction
    """
    env_path = (env_path or "").strip()
    build_dir = (build_dir or "").strip()
    if not env_path or not build_dir:
        log("Runtime env link skipped: env_path or build_dir missing")
        return False

    env_p = Path(env_path)
    build_p = Path(build_dir)
    if not build_p.exists():
        log(f"Runtime env publish skipped: build_dir not found: {build_p}")
        return False

    try:
        if env_p.exists() or env_p.is_symlink():
            is_link = _is_reparse_point(env_p)
            try:
                same_target = env_p.resolve(strict=True) == build_p.resolve(strict=True)
            except Exception:
                same_target = False
            if is_link and same_target:
                log(f"Runtime env junction already correct: {env_p} -> {build_p}")
                return True
            log(f"Runtime env path exists but is not the expected junction: {env_p}")
            _remove_path_for_relink(env_p, log)
            log(f"Runtime env path cleared for relink: {env_p}")

        env_p.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(env_p), str(build_p)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if result.stdout:
            log(result.stdout.strip())
        if result.stderr:
            log(result.stderr.strip())
        if result.returncode == 0 and env_p.exists():
            log(f"Runtime env junction created: {env_p} -> {build_p}")
            return True
        raise RuntimeError(f"mklink failed with exit code {result.returncode}")
    except Exception as e:
        log(f"Runtime env junction creation failed: {e}")
        return False

def update_comfy_env(python_path: str, env_mode: str, log):
    target_version = get_target_comfy_env_version(env_mode)
    log(f"Selected comfy-env target version for {(env_mode or 'local').lower()}: {target_version}")
    run_stream([python_path, "-m", "pip", "install", "--upgrade", f"comfy-env=={target_version}"], log=log)


def resolve_comfy_env_exe(python_path: str):
    py = Path(python_path)
    for c in [py.parent / "Scripts" / "comfy-env.exe", py.parent / "Scripts" / "comfy-env"]:
        if c.exists():
            return c
    return None


def log_recovery_matrix_policy(log, header=None):
    if header:
        log(header)
    log(f"Embedded validated recovery matrix: {EMBEDDED_VALIDATED_RECOVERY_MATRIX}")
    log(f"Historical torch 2.7 hypothesis: {HISTORICAL_TORCH27_HYPOTHESIS}")


def cleanup_current_unirig_env(unirig_path: str, log):
    current_envs = detect_old_unirig_env(unirig_path)
    if not current_envs:
        log("Recovery cleanup: no existing UniRig env found")
        return False
    log(f"Recovery cleanup: removing {len(current_envs)} current UniRig env(s) before retry")
    remove_old_env(current_envs, log)
    return True


def get_comfy_env_install_candidates(python_path: str, env_mode: str):
    candidates = []
    comfy_env_exe = resolve_comfy_env_exe(python_path)
    if comfy_env_exe:
        candidates.append({
            "cmd": [str(comfy_env_exe), "install"],
            "label": "exe",
            "description": "comfy-env executable",
        })

    candidates.append({
        "cmd": [python_path, "-m", "comfy_env.cli", "install"],
        "label": "cli",
        "description": "python -m comfy_env.cli install",
    })

    # Legacy __main__ invocation stays available only for embedded as a last-resort fallback.
    # Desktop / venv mode must never use it because it is known to fail with comfy-env 0.2.61.
    if (env_mode or "").lower() == "embedded":
        candidates.append({
            "cmd": [python_path, "-m", "comfy_env", "install"],
            "label": "legacy",
            "description": "python -m comfy_env install",
        })

    return candidates


def find_unirig_env_python_from_path(unirig_path: str, extra_paths=None) -> str:
    search_paths = []
    if extra_paths:
        search_paths.extend(extra_paths)
    if unirig_path:
        nodes_dir = Path(unirig_path) / "nodes"
        if nodes_dir.exists():
            envs = sorted([p for p in nodes_dir.glob("_env_*") if p.exists()], key=lambda p: p.stat().st_mtime, reverse=True)
            search_paths.extend(str(p) for p in envs)
    return resolve_env_python_from_paths(search_paths)


def is_recoverable_partial_install(output_lines, unirig_path: str):
    joined_output = "\n".join(output_lines)
    paths = extract_install_paths(output_lines)
    env_python = find_unirig_env_python_from_path(unirig_path, [paths.get("env_path"), paths.get("build_dir")])
    flash_attn_wheel_missing = (
        "No wheel for flash-attn" in joined_output
        or "Missing wheel: flash-attn" in joined_output
    )
    flash_attn_timeout = (
        ("ReadTimeoutError" in joined_output or "Read timed out" in joined_output or "The read operation timed out" in joined_output)
        and ("flash-attn" in joined_output or "flash_attn" in joined_output)
    )
    pixi_metadata_panic = (
        "could not create site-packages" in joined_output
        and "expected version to start with a number" in joined_output
    )
    if flash_attn_wheel_missing and env_python:
        return True, env_python, "flash_attn_missing"
    if flash_attn_timeout and env_python:
        return True, env_python, "flash_attn_timeout"
    if pixi_metadata_panic and env_python:
        return True, env_python, "pixi_metadata_panic"
    return False, env_python, ""


def install_unirig_env(python_path: str, unirig_path: str, env_mode: str, log):
    unirig = Path(unirig_path)
    normalized_mode = (env_mode or "local").lower()
    candidates = get_comfy_env_install_candidates(python_path, normalized_mode)

    def _is_network_failure(output: str) -> bool:
        lowered = (output or "").lower()
        patterns = [
            "failed to fetch",
            "request failed after 3 retries",
            "os error 10054",
            "readtimeouterror",
            "read timed out",
            "the read operation timed out",
            "download.pytorch.org",
            "release-assets.githubusercontent.com",
            "client error (connect)",
            "connection aborted",
            "connection reset",
            "connection broken",
        ]
        return any(pattern in lowered for pattern in patterns)

    last_error = None
    max_network_attempts = 3
    for index, candidate in enumerate(candidates, start=1):
        cmd = candidate["cmd"]
        label = candidate["label"]
        description = candidate["description"]
        network_attempt = 1
        while network_attempt <= max_network_attempts:
            try:
                if label == "legacy":
                    log("Embedded legacy fallback: python -m comfy_env install")
                elif label == "cli":
                    log(f"Using CLI fallback ({index}/{len(candidates)}): {description}")
                else:
                    log(f"Using {description} ({index}/{len(candidates)})")
                if network_attempt > 1:
                    log(f"[retry] comfy-env install attempt {network_attempt}/{max_network_attempts} after transient network failure")
                output_lines = run_stream(cmd, cwd=str(unirig), log=log)
                paths = extract_install_paths(output_lines)
                env_python = find_unirig_env_python_from_path(unirig_path, [paths.get("env_path"), paths.get("build_dir")])
                return {"status": "ok", "reason": "ok", "env_python": env_python, "env_path": paths.get("env_path", ""), "build_dir": paths.get("build_dir", ""), "output_lines": output_lines}
            except CommandExecutionError as e:
                last_error = e
                joined_output = "\n".join(e.output_lines)
                paths = extract_install_paths(e.output_lines)
                env_python = find_unirig_env_python_from_path(unirig_path, [paths.get("env_path"), paths.get("build_dir")])
                flash_attn_wheel_missing = (
                    "No wheel for flash-attn" in joined_output
                    or "Missing wheel: flash-attn" in joined_output
                )
                flash_attn_timeout = (
                    ("ReadTimeoutError" in joined_output or "Read timed out" in joined_output or "The read operation timed out" in joined_output)
                    and ("flash-attn" in joined_output or "flash_attn" in joined_output)
                )
                pixi_metadata_panic = (
                    "could not create site-packages" in joined_output
                    and "expected version to start with a number" in joined_output
                )
                network_failure = _is_network_failure(joined_output)
                if network_failure and network_attempt < max_network_attempts:
                    log(f"Attempt failed: {' '.join(cmd)}")
                    log("⚠ Transient network failure detected during comfy-env install.")
                    log(f"⚠ Automatic retry in 5 seconds ({network_attempt}/{max_network_attempts})...")
                    time.sleep(5)
                    network_attempt += 1
                    continue
                if network_failure and network_attempt >= max_network_attempts:
                    log(f"Attempt failed: {' '.join(cmd)}")
                    log("❌ Échec réseau pendant le téléchargement des dépendances PyTorch / UniRig.")
                    log("❌ Vérifiez votre connexion internet, puis relancez OneClick Install.")
                if flash_attn_wheel_missing and env_python:
                    log(f"Attempt failed: {' '.join(cmd)}")
                    log("⚠ comfy-env stopped because flash-attn wheel is unavailable for this target.")
                    log_recovery_matrix_policy(log, "⚠ Switching to embedded-validated recovery policy.")
                    log(f"⚠ Partial UniRig env detected: {env_python}")
                    log("⚠ Continuing with post-install checks and targeted fallback installs.")
                    return {"status": "partial", "reason": "flash_attn_missing", "env_python": env_python, "env_path": paths.get("env_path", ""), "build_dir": paths.get("build_dir", ""), "output_lines": e.output_lines}
                if flash_attn_timeout and env_python:
                    log(f"Attempt failed: {' '.join(cmd)}")
                    log("⚠ comfy-env timed out while downloading flash-attn.")
                    log("⚠ Retrying flash-attn later with targeted fallback inside the isolated env.")
                    log_recovery_matrix_policy(log, "⚠ Switching to embedded-validated recovery policy.")
                    log(f"⚠ Partial UniRig env detected: {env_python}")
                    return {"status": "partial", "reason": "flash_attn_timeout", "env_python": env_python, "env_path": paths.get("env_path", ""), "build_dir": paths.get("build_dir", ""), "output_lines": e.output_lines}
                if pixi_metadata_panic:
                    log(f"Attempt failed: {' '.join(cmd)}")
                    log("⚠ pixi failed while parsing wheel metadata during UniRig environment build.")
                    log_recovery_matrix_policy(log, "⚠ Switching to recovery policy.")
                    if env_python:
                        log(f"⚠ Partial UniRig env detected: {env_python}")
                    else:
                        log("⚠ No usable env python detected yet, but this panic is treated as recoverable.")
                    return {"status": "partial", "reason": "pixi_metadata_panic", "env_python": env_python, "env_path": paths.get("env_path", ""), "build_dir": paths.get("build_dir", ""), "output_lines": e.output_lines}
                log(f"Attempt failed: {' '.join(cmd)}")
                log(str(e))
                break
            except Exception as e:
                last_error = e
                log(f"Attempt failed: {' '.join(cmd)}")
                log(str(e))
                break

    raise RuntimeError(
        f"Unable to run comfy-env install in {normalized_mode} mode with any supported command: {last_error}"
    )


def patch_mesh_io(unirig_path: str, log):
    mesh = Path(unirig_path) / "nodes" / "mesh_io.py"
    if not mesh.exists():
        return
    content = mesh.read_text(encoding="utf-8")
    old_block = '''"file_path": (mesh_files, {
                    "tooltip": "Mesh file to load. Refresh the node after changing source_folder."
                }),'''
    new_block = '''"file_path": ("STRING", {
                    "default": "3d/test.glb",
                    "multiline": False,
                    "tooltip": "Relative or absolute mesh path."
                }),'''
    if new_block in content:
        log("mesh_io.py already patched")
        return
    if old_block not in content:
        log("mesh_io.py patch block not found")
        return
    backup = mesh.with_suffix(".py.pre_patch_backup")
    if not backup.exists():
        backup.write_text(content, encoding="utf-8")
    mesh.write_text(content.replace(old_block, new_block), encoding="utf-8")
    log("mesh_io.py patched")




def patch_direct_preprocess_runtime_bridge(unirig_path: str, log):
    target = Path(unirig_path) / "nodes" / "unirig" / "direct_preprocess.py"
    if not target.exists():
        log("direct_preprocess.py not found, runtime bpy bridge patch skipped")
        return

    content = target.read_text(encoding="utf-8")
    marker = "UNIRIG_RUNTIME_BPY_BRIDGE_V1"
    if marker in content:
        log("direct_preprocess.py runtime bpy bridge already patched")
        return

    anchor = 'log = logging.getLogger("unirig")\n'
    import_block = (
        '    # Lazy import to avoid torch_cluster conflict\n'
        '    try:\n'
        '        import bpy\n'
        '    except ModuleNotFoundError:\n'
        '        log.info("bpy missing in ComfyUI runtime, switching to UniRig env subprocess")\n'
        '        return _run_bpy_subprocess(input_file, output_npz, target_face_count)\n'
    )

    if anchor not in content:
        log("direct_preprocess.py patch anchor not found")
        return

    if '    import bpy\n' not in content:
        log("direct_preprocess.py bpy import block not found")
        return

    helper_block = """
# UNIRIG_RUNTIME_BPY_BRIDGE_V1
def _find_runtime_env_python() -> str:
    nodes_dir = Path(__file__).resolve().parent.parent
    candidates = []
    for env_dir in sorted(nodes_dir.glob("_env_*"), reverse=True):
        candidates.extend([
            env_dir / ".pixi" / "envs" / "default" / "python.exe",
            env_dir / "python.exe",
        ])
        try:
            resolved = env_dir.resolve(strict=True)
            candidates.extend([
                resolved / ".pixi" / "envs" / "default" / "python.exe",
                resolved / "python.exe",
            ])
        except Exception:
            pass

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return ""


def _load_npz_result(output_npz: str) -> dict:
    data = np.load(output_npz, allow_pickle=True)
    uv_coords = data["uv_coords"] if "uv_coords" in data.files and data["uv_coords"].size else None
    uv_faces = data["uv_faces"] if "uv_faces" in data.files and data["uv_faces"].size else None
    material_name = str(data["material_name"]) if "material_name" in data.files else None
    texture_path = str(data["texture_path"]) if "texture_path" in data.files else None
    texture_data_base64 = str(data["texture_data_base64"]) if "texture_data_base64" in data.files else ""
    texture_format = str(data["texture_format"]) if "texture_format" in data.files else ""
    texture_width = int(data["texture_width"]) if "texture_width" in data.files else 0
    texture_height = int(data["texture_height"]) if "texture_height" in data.files else 0
    return {
        "vertices": data["vertices"],
        "vertex_normals": data["vertex_normals"],
        "faces": data["faces"],
        "face_normals": data["face_normals"],
        "uv_coords": uv_coords,
        "uv_faces": uv_faces,
        "material_name": material_name,
        "texture_path": texture_path,
        "texture_data_base64": texture_data_base64,
        "texture_format": texture_format,
        "texture_width": texture_width,
        "texture_height": texture_height,
    }


def _run_bpy_subprocess(input_file: str, output_npz: str, target_face_count: int) -> dict:
    import subprocess

    env_python = _find_runtime_env_python()
    if not env_python:
        raise ModuleNotFoundError("bpy not available in ComfyUI runtime and UniRig env python not found")

    cmd = [
        env_python,
        str(Path(__file__).resolve()),
        "--unirig-bpy-subprocess",
        input_file,
        output_npz,
        str(int(target_face_count)),
    ]
    env = os.environ.copy()
    env["UNIRIG_BPY_SUBPROCESS"] = "1"

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )
    if result.stdout:
        for line in result.stdout.splitlines():
            log.info("[bpy-subprocess] %s", line)
    if result.stderr:
        for line in result.stderr.splitlines():
            log.info("[bpy-subprocess][stderr] %s", line)
    if result.returncode != 0:
        raise RuntimeError(f"bpy subprocess failed with exit code {result.returncode}")
    if not Path(output_npz).exists():
        raise RuntimeError("bpy subprocess completed but output NPZ was not created")
    return _load_npz_result(output_npz)

"""

    main_block = """

def _cli_main() -> int:
    import sys

    if len(sys.argv) >= 5 and sys.argv[1] == "--unirig-bpy-subprocess":
        _, _, input_file, output_npz, target_face_count = sys.argv[:5]
        preprocess_mesh(input_file, output_npz, int(target_face_count))
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli_main())
"""

    backup = target.with_suffix('.py.runtime_bpy_backup')
    if not backup.exists():
        backup.write_text(content, encoding='utf-8')

    new_content = content.replace(anchor, anchor + helper_block, 1)
    new_content = new_content.replace('    # Lazy import to avoid torch_cluster conflict\n    import bpy\n', import_block, 1)
    if '_cli_main()' not in new_content:
        new_content = new_content.rstrip() + main_block
    target.write_text(new_content, encoding='utf-8')
    log("direct_preprocess.py runtime bpy bridge patched")



def patch_direct_runtime_bridge(unirig_path: str, log):
    target = Path(unirig_path) / "nodes" / "unirig" / "direct.py"
    if not target.exists():
        log("direct.py not found, runtime direct bridge patch skipped")
        return

    content = target.read_text(encoding="utf-8")
    marker_v3 = "UNIRIG_RUNTIME_DIRECT_BRIDGE_V3"
    marker_v2 = "UNIRIG_RUNTIME_DIRECT_BRIDGE_V2"
    marker_v1 = "UNIRIG_RUNTIME_DIRECT_BRIDGE_V1"
    backup = target.with_suffix('.py.runtime_direct_backup')

    if marker_v3 in content:
        log("direct.py runtime direct bridge already patched")
        return

    if (marker_v2 in content or marker_v1 in content) and backup.exists():
        content = backup.read_text(encoding='utf-8')

    anchor = 'log = logging.getLogger("unirig")\n'
    if anchor not in content:
        log("direct.py patch anchor not found")
        return

    helper_block = """
# UNIRIG_RUNTIME_DIRECT_BRIDGE_V3
import os
from pathlib import Path


def _find_runtime_env_python() -> str:
    nodes_dir = Path(__file__).resolve().parent.parent
    candidates = []
    for env_dir in sorted(nodes_dir.glob("_env_*"), reverse=True):
        candidates.extend([
            env_dir / ".pixi" / "envs" / "default" / "python.exe",
            env_dir / "python.exe",
        ])
        try:
            resolved = env_dir.resolve(strict=True)
            candidates.extend([
                resolved / ".pixi" / "envs" / "default" / "python.exe",
                resolved / "python.exe",
            ])
        except Exception:
            pass

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return ""


def _build_clean_subprocess_env(env_python: str) -> dict:
    runtime_root = Path(__file__).resolve().parents[4]
    env_python_path = Path(env_python)
    env_root = env_python_path.parent.parent.parent  # .../.pixi/envs/default -> env root

    keep_prefixes = (
        "SYSTEM",
        "WINDIR",
        "TEMP",
        "TMP",
        "COMSPEC",
        "PATHEXT",
        "NUMBER_OF_PROCESSORS",
        "PROCESSOR_",
        "CUDA",
        "NVIDIA",
        "NV_",
        "USERPROFILE",
        "HOMEDRIVE",
        "HOMEPATH",
        "APPDATA",
        "LOCALAPPDATA",
        "PROGRAMDATA",
    )

    clean_env = {}
    for key, value in os.environ.items():
        upper = key.upper()
        if upper in {"PATH", "SYSTEMROOT"}:
            continue
        if upper in {"PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "__PYVENV_LAUNCHER__", "PIP_REQUIRE_VIRTUALENV"}:
            continue
        if upper.startswith(keep_prefixes):
            clean_env[key] = value

    path_entries = []
    # Prefer UniRig env executables and DLL locations first.
    for candidate in [
        env_python_path.parent,
        env_root,
        env_root / "Library" / "bin",
        env_root / "Scripts",
        env_root / "bin",
    ]:
        candidate_str = str(candidate)
        if candidate.exists() and candidate_str not in path_entries:
            path_entries.append(candidate_str)

    # Then preserve the original PATH for system tools and drivers.
    original_path = os.environ.get("PATH", "")
    if original_path:
        for entry in original_path.split(os.pathsep):
            entry = entry.strip()
            if not entry:
                continue
            norm = entry.replace('/', '\\').lower().rstrip('\\')
            if 'comfyui_desktop\\venv\\lib\\site-packages' in norm:
                continue
            if 'comfyui_desktop\\venv\\scripts' in norm:
                continue
            if entry not in path_entries:
                path_entries.append(entry)

    clean_env["PATH"] = os.pathsep.join(path_entries)
    clean_env["PYTHONPATH"] = str(runtime_root)
    clean_env["PYTHONNOUSERSITE"] = "1"
    clean_env["UNIRIG_DIRECT_SUBPROCESS"] = "1"
    clean_env["UNIRIG_DIRECT_ENV_PYTHON"] = str(env_python_path)
    clean_env["UNIRIG_DIRECT_RUNTIME_ROOT"] = str(runtime_root)
    return clean_env


def _run_direct_subprocess(mode: str, payload: dict):
    import pickle
    import subprocess
    import tempfile

    env_python = _find_runtime_env_python()
    if not env_python:
        raise ModuleNotFoundError(f"UniRig env python not found for direct {mode} subprocess")

    with tempfile.TemporaryDirectory() as td:
        in_file = Path(td) / "input.pkl"
        out_file = Path(td) / "output.pkl"
        with open(in_file, "wb") as f:
            pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)

        cmd = [
            env_python,
            str(Path(__file__).resolve()),
            "--unirig-direct-subprocess",
            mode,
            str(in_file),
            str(out_file),
        ]
        env = _build_clean_subprocess_env(env_python)
        log.info("[direct-subprocess] isolated env prepared for ComfyUI runtime")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env,
            cwd=str(Path(__file__).resolve().parents[4]),
            check=False,
        )
        if result.stdout:
            for line in result.stdout.splitlines():
                log.info("[direct-subprocess] %s", line)
        if result.stderr:
            for line in result.stderr.splitlines():
                log.info("[direct-subprocess][stderr] %s", line)
        if result.returncode != 0:
            raise RuntimeError(f"direct subprocess {mode} failed with exit code {result.returncode}")
        if not out_file.exists():
            raise RuntimeError(f"direct subprocess {mode} completed but output was not created")
        with open(out_file, "rb") as f:
            return pickle.load(f)


def _runtime_missing_direct_deps() -> bool:
    try:
        import torch_cluster  # noqa: F401
        import cumm  # noqa: F401
        import spconv  # noqa: F401
        return False
    except ModuleNotFoundError:
        return True


def _cli_main() -> int:
    import pickle
    import sys

    if len(sys.argv) >= 5 and sys.argv[1] == "--unirig-direct-subprocess":
        print(f"sys.executable={sys.executable}")
        print(f"cwd={os.getcwd()}")
        for idx, entry in enumerate(sys.path[:8]):
            print(f"sys.path[{idx}]={entry}")
        mode = sys.argv[2]
        in_file = sys.argv[3]
        out_file = sys.argv[4]
        with open(in_file, "rb") as f:
            payload = pickle.load(f)
        if mode == "skeleton":
            result = _ORIG_predict_skeleton_from_mesh(**payload)
        elif mode == "skinning":
            result = _ORIG_predict_skinning(**payload)
        else:
            raise ValueError(f"Unknown direct subprocess mode: {mode}")
        with open(out_file, "wb") as f:
            pickle.dump(result, f, protocol=pickle.HIGHEST_PROTOCOL)
        return 0
    return 0


"""
    wrapper_block = """

_ORIG_predict_skeleton_from_mesh = predict_skeleton_from_mesh
_ORIG_predict_skinning = predict_skinning


@torch.no_grad()
def predict_skeleton_from_mesh(
    vertices: np.ndarray,
    faces: np.ndarray,
    skeleton_checkpoint: str,
    num_samples: int = 2048,
    cls: str = "articulationxl",
    max_new_tokens: int = 2048,
    seed: int = 42,
    dtype=None,
    attn_backend: str = "auto",
):
    if os.environ.get("UNIRIG_DIRECT_SUBPROCESS") != "1" and _runtime_missing_direct_deps():
        log.info("UniRig direct deps missing in ComfyUI runtime, switching skeleton inference to UniRig env subprocess")
        payload = {
            "vertices": vertices,
            "faces": faces,
            "skeleton_checkpoint": skeleton_checkpoint,
            "num_samples": num_samples,
            "cls": cls,
            "max_new_tokens": max_new_tokens,
            "seed": seed,
            "dtype": dtype,
            "attn_backend": attn_backend,
        }
        return _run_direct_subprocess("skeleton", payload)
    return _ORIG_predict_skeleton_from_mesh(
        vertices=vertices,
        faces=faces,
        skeleton_checkpoint=skeleton_checkpoint,
        num_samples=num_samples,
        cls=cls,
        max_new_tokens=max_new_tokens,
        seed=seed,
        dtype=dtype,
        attn_backend=attn_backend,
    )


@torch.no_grad()
def predict_skinning(
    vertices: np.ndarray,
    normals: np.ndarray,
    joints: np.ndarray,
    parents: np.ndarray,
    checkpoint_path: str,
    faces: Optional[np.ndarray] = None,
    tails: Optional[np.ndarray] = None,
    voxel_grid_size: int = 196,
    dtype=None,
    attn_backend: str = "auto",
):
    if os.environ.get("UNIRIG_DIRECT_SUBPROCESS") != "1" and _runtime_missing_direct_deps():
        log.info("UniRig direct deps missing in ComfyUI runtime, switching skinning inference to UniRig env subprocess")
        payload = {
            "vertices": vertices,
            "normals": normals,
            "joints": joints,
            "parents": parents,
            "checkpoint_path": checkpoint_path,
            "faces": faces,
            "tails": tails,
            "voxel_grid_size": voxel_grid_size,
            "dtype": dtype,
            "attn_backend": attn_backend,
        }
        return _run_direct_subprocess("skinning", payload)
    return _ORIG_predict_skinning(
        vertices=vertices,
        normals=normals,
        joints=joints,
        parents=parents,
        checkpoint_path=checkpoint_path,
        faces=faces,
        tails=tails,
        voxel_grid_size=voxel_grid_size,
        dtype=dtype,
        attn_backend=attn_backend,
    )


if __name__ == "__main__":
    raise SystemExit(_cli_main())
"""

    if not backup.exists():
        backup.write_text(content, encoding='utf-8')

    new_content = content.replace(anchor, anchor + helper_block, 1)
    if '_ORIG_predict_skeleton_from_mesh = predict_skeleton_from_mesh' not in new_content:
        new_content = new_content.rstrip() + wrapper_block
    target.write_text(new_content, encoding='utf-8')
    log("direct.py runtime direct bridge patched")




def patch_direct_runtime_bridge_syntax_fix(unirig_path: str, log):
    target = Path(unirig_path) / "nodes" / "unirig" / "direct.py"
    if not target.exists():
        log("direct.py not found, syntax fix skipped")
        return
    content = target.read_text(encoding="utf-8")
    bad = "norm = entry.replace('/', '\\').lower().rstrip('\\')"
    # Recover accidental broken line if present in file
    broken = "norm = entry.replace('/', '\').lower().rstrip('\\')"
    broken2 = "norm = entry.replace('/', '\\').lower().rstrip('\\\\')"  # no-op marker
    fixed = "norm = entry.replace('/', '\\\\').lower().rstrip('\\\\')"
    if fixed in content:
        log("direct.py syntax fix already present")
        return
    if "norm = entry.replace('/', '\').lower().rstrip('\')" in content:
        content = content.replace("norm = entry.replace('/', '\').lower().rstrip('\')", fixed)
        target.write_text(content, encoding="utf-8")
        log("direct.py syntax fix applied")
        return
    # Best-effort repair for malformed escaping
    content2 = content.replace("norm = entry.replace('/', '\').lower().rstrip('\\')", fixed)
    content2 = content2.replace("norm = entry.replace('/', '\\').lower().rstrip('\\')", fixed)
    if content2 != content:
        target.write_text(content2, encoding="utf-8")
        log("direct.py syntax fix applied")
    else:
        log("direct.py syntax fix not needed")


def patch_skeleton_extraction_autonomous(unirig_path: str, log):
    target = Path(unirig_path) / "nodes" / "skeleton_extraction.py"
    if not target.exists():
        log("skeleton_extraction.py not found, subprocess patch skipped")
        return
    marker = "_run_direct_inference_subprocess"
    current = target.read_text(encoding="utf-8")
    desired = '"""\nSkeleton extraction nodes for UniRig.\n\nUses comfy-env isolated environment for GPU dependencies.\nUses direct Python inference with bpy for mesh preprocessing.\n"""\n\nimport os\nimport sys\nimport tempfile\nimport numpy as np\nfrom trimesh import Trimesh\nimport time\nimport folder_paths\nimport logging\nimport pickle\nimport subprocess\nfrom pathlib import Path\n\nlog = logging.getLogger("unirig")\nTARGET_FACE_COUNT = 50000  # default for mesh decimation\n\ntry:\n    from .base import (\n        UNIRIG_PATH,\n        UNIRIG_MODELS_DIR,\n        decode_texture_to_comfy_image,\n        create_placeholder_texture,\n    )\nexcept ImportError:\n    from base import (\n        UNIRIG_PATH,\n        UNIRIG_MODELS_DIR,\n        decode_texture_to_comfy_image,\n        create_placeholder_texture,\n    )\n\n# VRoid to Mixamo bone name mapping (52 bones, 1:1 correspondence)\nVROID_TO_MIXAMO_BONE_MAP = {\n    # Body (22 bones)\n    "J_Bip_C_Hips": "mixamorig:Hips",\n    "J_Bip_C_Spine": "mixamorig:Spine",\n    "J_Bip_C_Chest": "mixamorig:Spine1",\n    "J_Bip_C_UpperChest": "mixamorig:Spine2",\n    "J_Bip_C_Neck": "mixamorig:Neck",\n    "J_Bip_C_Head": "mixamorig:Head",\n    "J_Bip_L_Shoulder": "mixamorig:LeftShoulder",\n    "J_Bip_L_UpperArm": "mixamorig:LeftArm",\n    "J_Bip_L_LowerArm": "mixamorig:LeftForeArm",\n    "J_Bip_L_Hand": "mixamorig:LeftHand",\n    "J_Bip_R_Shoulder": "mixamorig:RightShoulder",\n    "J_Bip_R_UpperArm": "mixamorig:RightArm",\n    "J_Bip_R_LowerArm": "mixamorig:RightForeArm",\n    "J_Bip_R_Hand": "mixamorig:RightHand",\n    "J_Bip_L_UpperLeg": "mixamorig:LeftUpLeg",\n    "J_Bip_L_LowerLeg": "mixamorig:LeftLeg",\n    "J_Bip_L_Foot": "mixamorig:LeftFoot",\n    "J_Bip_L_ToeBase": "mixamorig:LeftToeBase",\n    "J_Bip_R_UpperLeg": "mixamorig:RightUpLeg",\n    "J_Bip_R_LowerLeg": "mixamorig:RightLeg",\n    "J_Bip_R_Foot": "mixamorig:RightFoot",\n    "J_Bip_R_ToeBase": "mixamorig:RightToeBase",\n    # Left Hand (15 bones)\n    "J_Bip_L_Thumb1": "mixamorig:LeftHandThumb1",\n    "J_Bip_L_Thumb2": "mixamorig:LeftHandThumb2",\n    "J_Bip_L_Thumb3": "mixamorig:LeftHandThumb3",\n    "J_Bip_L_Index1": "mixamorig:LeftHandIndex1",\n    "J_Bip_L_Index2": "mixamorig:LeftHandIndex2",\n    "J_Bip_L_Index3": "mixamorig:LeftHandIndex3",\n    "J_Bip_L_Middle1": "mixamorig:LeftHandMiddle1",\n    "J_Bip_L_Middle2": "mixamorig:LeftHandMiddle2",\n    "J_Bip_L_Middle3": "mixamorig:LeftHandMiddle3",\n    "J_Bip_L_Ring1": "mixamorig:LeftHandRing1",\n    "J_Bip_L_Ring2": "mixamorig:LeftHandRing2",\n    "J_Bip_L_Ring3": "mixamorig:LeftHandRing3",\n    "J_Bip_L_Little1": "mixamorig:LeftHandPinky1",\n    "J_Bip_L_Little2": "mixamorig:LeftHandPinky2",\n    "J_Bip_L_Little3": "mixamorig:LeftHandPinky3",\n    # Right Hand (15 bones)\n    "J_Bip_R_Thumb1": "mixamorig:RightHandThumb1",\n    "J_Bip_R_Thumb2": "mixamorig:RightHandThumb2",\n    "J_Bip_R_Thumb3": "mixamorig:RightHandThumb3",\n    "J_Bip_R_Index1": "mixamorig:RightHandIndex1",\n    "J_Bip_R_Index2": "mixamorig:RightHandIndex2",\n    "J_Bip_R_Index3": "mixamorig:RightHandIndex3",\n    "J_Bip_R_Middle1": "mixamorig:RightHandMiddle1",\n    "J_Bip_R_Middle2": "mixamorig:RightHandMiddle2",\n    "J_Bip_R_Middle3": "mixamorig:RightHandMiddle3",\n    "J_Bip_R_Ring1": "mixamorig:RightHandRing1",\n    "J_Bip_R_Ring2": "mixamorig:RightHandRing2",\n    "J_Bip_R_Ring3": "mixamorig:RightHandRing3",\n    "J_Bip_R_Little1": "mixamorig:RightHandPinky1",\n    "J_Bip_R_Little2": "mixamorig:RightHandPinky2",\n    "J_Bip_R_Little3": "mixamorig:RightHandPinky3",\n}\n\n# VRoid to SMPL bone mapping (22 joints - maps VRoid bones to SMPL joint names)\nVROID_TO_SMPL_BONE_MAP = {\n    "J_Bip_C_Hips": "Pelvis",           # 0\n    "J_Bip_L_UpperLeg": "L_Hip",         # 1\n    "J_Bip_R_UpperLeg": "R_Hip",         # 2\n    "J_Bip_C_Spine": "Spine1",           # 3\n    "J_Bip_L_LowerLeg": "L_Knee",        # 4\n    "J_Bip_R_LowerLeg": "R_Knee",        # 5\n    "J_Bip_C_Chest": "Spine2",           # 6\n    "J_Bip_L_Foot": "L_Ankle",           # 7\n    "J_Bip_R_Foot": "R_Ankle",           # 8\n    "J_Bip_C_UpperChest": "Spine3",      # 9\n    "J_Bip_L_ToeBase": "L_Foot",         # 10\n    "J_Bip_R_ToeBase": "R_Foot",         # 11\n    "J_Bip_C_Neck": "Neck",              # 12\n    "J_Bip_L_Shoulder": "L_Collar",      # 13\n    "J_Bip_R_Shoulder": "R_Collar",      # 14\n    "J_Bip_C_Head": "Head",              # 15\n    "J_Bip_L_UpperArm": "L_Shoulder",    # 16\n    "J_Bip_R_UpperArm": "R_Shoulder",    # 17\n    "J_Bip_L_LowerArm": "L_Elbow",       # 18\n    "J_Bip_R_LowerArm": "R_Elbow",       # 19\n    "J_Bip_L_Hand": "L_Wrist",           # 20\n    "J_Bip_R_Hand": "R_Wrist",           # 21\n}\n\n# SMPL joint names in order (22 joints)\nSMPL_JOINT_NAMES = [\n    \'Pelvis\', \'L_Hip\', \'R_Hip\', \'Spine1\', \'L_Knee\', \'R_Knee\',\n    \'Spine2\', \'L_Ankle\', \'R_Ankle\', \'Spine3\', \'L_Foot\', \'R_Foot\',\n    \'Neck\', \'L_Collar\', \'R_Collar\', \'Head\', \'L_Shoulder\', \'R_Shoulder\',\n    \'L_Elbow\', \'R_Elbow\', \'L_Wrist\', \'R_Wrist\'\n]\n\n# SMPL parent hierarchy (22 joints) - index of parent for each joint\nSMPL_PARENTS = [\n    -1,  # 0: Pelvis (root)\n    0,   # 1: L_Hip -> Pelvis\n    0,   # 2: R_Hip -> Pelvis\n    0,   # 3: Spine1 -> Pelvis\n    1,   # 4: L_Knee -> L_Hip\n    2,   # 5: R_Knee -> R_Hip\n    3,   # 6: Spine2 -> Spine1\n    4,   # 7: L_Ankle -> L_Knee\n    5,   # 8: R_Ankle -> R_Knee\n    6,   # 9: Spine3 -> Spine2\n    7,   # 10: L_Foot -> L_Ankle\n    8,   # 11: R_Foot -> R_Ankle\n    9,   # 12: Neck -> Spine3\n    9,   # 13: L_Collar -> Spine3\n    9,   # 14: R_Collar -> Spine3\n    12,  # 15: Head -> Neck\n    13,  # 16: L_Shoulder -> L_Collar\n    14,  # 17: R_Shoulder -> R_Collar\n    16,  # 18: L_Elbow -> L_Shoulder\n    17,  # 19: R_Elbow -> R_Shoulder\n    18,  # 20: L_Wrist -> L_Elbow\n    19,  # 21: R_Wrist -> R_Elbow\n]\n\n# SMPL canonical bone directions (unit vectors pointing from head to tail)\n# These define how each bone should be oriented in rest pose\n# Coordinate system: Blender default (X=right, Y=forward, Z=up)\n# These get rotated to SMPL coords (Y-up) when skeleton_template="smpl"\n# For symmetric bones, L and R have mirrored X component (left/right)\nSMPL_BONE_DIRECTIONS = {\n    \'Pelvis\':     [0, 0, 1],      # Up +Z (toward spine)\n    \'L_Hip\':      [0, 0, -1],     # Down -Z (toward knee)\n    \'R_Hip\':      [0, 0, -1],     # Down -Z (toward knee)\n    \'Spine1\':     [0, 0, 1],      # Up +Z\n    \'L_Knee\':     [0, 0, -1],     # Down -Z (toward ankle)\n    \'R_Knee\':     [0, 0, -1],     # Down -Z (toward ankle)\n    \'Spine2\':     [0, 0, 1],      # Up +Z\n    \'L_Ankle\':    [0, 1, 0],      # Forward +Y (toward toe)\n    \'R_Ankle\':    [0, 1, 0],      # Forward +Y (toward toe)\n    \'Spine3\':     [0, 0, 1],      # Up +Z\n    \'L_Foot\':     [0, 1, 0],      # Forward +Y\n    \'R_Foot\':     [0, 1, 0],      # Forward +Y\n    \'Neck\':       [0, 0, 1],      # Up +Z\n    \'L_Collar\':   [1, 0, 0],      # Left +X (toward shoulder)\n    \'R_Collar\':   [-1, 0, 0],     # Right -X (toward shoulder)\n    \'Head\':       [0, 0, 1],      # Up +Z\n    \'L_Shoulder\': [1, 0, 0],      # Left +X (toward elbow)\n    \'R_Shoulder\': [-1, 0, 0],     # Right -X (toward elbow)\n    \'L_Elbow\':    [1, 0, 0],      # Left +X (toward wrist)\n    \'R_Elbow\':    [-1, 0, 0],     # Right -X (toward wrist)\n    \'L_Wrist\':    [1, 0, 0],      # Left +X (toward hand)\n    \'R_Wrist\':    [-1, 0, 0],     # Right -X (toward hand)\n}\n\n# Default bone length for SMPL (used when computing tails)\nSMPL_DEFAULT_BONE_LENGTH = 0.1\n\n# Direct inference module\ntry:\n    from .unirig import direct as _direct_inference_module\nexcept Exception as e:\n    log.info("Direct inference not available: %s", e)\n    _direct_inference_module = None\n\n# Direct preprocessing module (bpy as Python module)\ntry:\n    from .unirig import direct_preprocess as _direct_preprocess_module\nexcept Exception as e:\n    log.info("Direct preprocessing not available: %s", e)\n    _direct_preprocess_module = None\n\n\ndef _get_direct_inference():\n    """Get the direct inference module for in-process model inference."""\n    return _direct_inference_module\n\n\ndef _get_direct_preprocess():\n    """Get the direct preprocessing module for in-process mesh preprocessing using bpy."""\n    return _direct_preprocess_module\n\n\ndef _find_unirig_env_python():\n    """Find the UniRig comfy-env Python interpreter published under nodes/_env_*."""\n    nodes_dir = Path(__file__).resolve().parent\n    candidates = []\n    for env_dir in sorted(nodes_dir.glob("_env_*"), reverse=True):\n        candidates.extend([\n            env_dir / ".pixi" / "envs" / "default" / "python.exe",\n            env_dir / "python.exe",\n        ])\n        try:\n            resolved = env_dir.resolve(strict=True)\n            candidates.extend([\n                resolved / ".pixi" / "envs" / "default" / "python.exe",\n                resolved / "python.exe",\n            ])\n        except Exception:\n            pass\n\n    for candidate in candidates:\n        if candidate.exists():\n            return str(candidate)\n    return ""\n\n\ndef _run_direct_inference_subprocess(mode: str, payload: dict):\n    """Run direct inference inside the UniRig comfy-env Python.\n\n    Important: run the module with `-m nodes.unirig.direct` instead of executing\n    direct.py as a script. Executing the file directly can break package-relative\n    imports in the isolated worker environment and only surfaces as exit code 1.\n    """\n    env_python = _find_unirig_env_python()\n    if not env_python:\n        raise RuntimeError("UniRig env python not found under nodes/_env_*")\n\n    nodes_dir = Path(__file__).resolve().parent\n    repo_root = nodes_dir.parent\n    comfy_root = repo_root.parent.parent\n\n    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:\n        td_path = Path(td)\n        in_file = td_path / "input.pkl"\n        out_file = td_path / "output.pkl"\n\n        with open(in_file, "wb") as f:\n            pickle.dump(payload, f, protocol=pickle.HIGHEST_PROTOCOL)\n\n        cmd = [\n            env_python,\n            "-m",\n            "nodes.unirig.direct",\n            "--unirig-direct-subprocess",\n            mode,\n            str(in_file),\n            str(out_file),\n        ]\n\n        env = os.environ.copy()\n        py_entries = [\n            str(comfy_root),\n            str(repo_root),\n            str(nodes_dir),\n        ]\n        current_pp = env.get("PYTHONPATH", "")\n        if current_pp:\n            py_entries.append(current_pp)\n        env["PYTHONPATH"] = os.pathsep.join(py_entries)\n        env["PYTHONNOUSERSITE"] = "1"\n\n        log.info("Launching direct %s subprocess with UniRig env: %s", mode, env_python)\n        log.info("Direct subprocess cwd: %s", repo_root)\n        log.info("Direct subprocess PYTHONPATH: %s", env["PYTHONPATH"])\n        log.info("Direct subprocess command: %s", " ".join(cmd))\n\n        result = subprocess.run(\n            cmd,\n            capture_output=True,\n            text=True,\n            encoding="utf-8",\n            errors="replace",\n            check=False,\n            cwd=str(repo_root),\n            env=env,\n        )\n\n        if result.stdout:\n            for line in result.stdout.splitlines():\n                log.info("[direct-subprocess] %s", line)\n        if result.stderr:\n            for line in result.stderr.splitlines():\n                log.info("[direct-subprocess][stderr] %s", line)\n\n        if result.returncode != 0:\n            stdout_tail = (result.stdout or "").strip()[-2000:]\n            stderr_tail = (result.stderr or "").strip()[-2000:]\n            raise RuntimeError(\n                f"Direct {mode} subprocess failed with exit code {result.returncode}\\n\\n"\n                f"STDOUT tail:\\n{stdout_tail or \'<empty>\'}\\n\\n"\n                f"STDERR tail:\\n{stderr_tail or \'<empty>\'}"\n            )\n        if not out_file.exists():\n            raise RuntimeError(f"Direct {mode} subprocess completed but output was not created")\n\n        with open(out_file, "rb") as f:\n            return pickle.load(f)\n\n\n\nclass UniRigExtractSkeletonNew:\n    """\n    Extract skeleton from mesh using UniRig (SIGGRAPH 2025).\n\n    Uses ML-based approach for high-quality semantic skeleton extraction.\n    Works on any mesh type: humans, animals, objects, cameras, etc.\n\n    Runs in isolated environment with GPU dependencies.\n    Requires pre-loaded model from UniRigLoadSkeletonModel.\n    """\n\n    @classmethod\n    def INPUT_TYPES(cls):\n        return {\n            "required": {\n                "trimesh": ("TRIMESH",),\n                "skeleton_model": ("UNIRIG_SKELETON_MODEL", {\n                    "tooltip": "Pre-loaded skeleton model (from UniRigLoadSkeletonModel) - REQUIRED"\n                }),\n                "seed": ("INT", {"default": 42, "min": 0, "max": 4294967295,\n                               "tooltip": "Random seed for skeleton generation variation"}),\n            },\n            "optional": {\n                "skeleton_template": (["vroid", "mixamo", "smpl", "articulationxl"], {\n                    "default": "mixamo",\n                    "tooltip": "Skeleton template: vroid (52 bones), mixamo (Mixamo-compatible 52 bones), smpl (22 joints, SMPL-compatible for direct motion application), articulationxl (generic/flexible)"\n                }),\n                "target_face_count": ("INT", {\n                    "default": 50000,\n                    "min": 10000,\n                    "max": 500000,\n                    "step": 10000,\n                    "tooltip": "Target face count for mesh decimation. Higher = preserve more detail, slower. Default: 50000"\n                }),\n            }\n        }\n\n    RETURN_TYPES = ("TRIMESH", "SKELETON", "IMAGE")\n    RETURN_NAMES = ("normalized_mesh", "skeleton", "texture_preview")\n    FUNCTION = "extract"\n    CATEGORY = "UniRig"\n\n    def extract(self, trimesh, skeleton_model, seed, skeleton_template="mixamo", target_face_count=None):\n        """Extract skeleton using UniRig with cached model only."""\n        total_start = time.time()\n        log.info("Starting skeleton extraction (cached model only)...")\n        log.info("Skeleton template: %s", skeleton_template)\n\n        # Store original template choice before any remapping\n        original_template = skeleton_template\n\n        # Track if we need to remap to mixamo or smpl naming\n        remap_to_mixamo = (skeleton_template == "mixamo")\n        remap_to_smpl = (skeleton_template == "smpl")\n\n        # If mixamo is requested, use vroid for extraction (model trained on vroid), then remap names\n        if skeleton_template == "mixamo":\n            skeleton_template = "vroid"\n            log.info("Mixamo requested, using vroid extraction + name remapping")\n\n        # If smpl is requested, use vroid for extraction, then filter to 22 SMPL joints\n        if skeleton_template == "smpl":\n            skeleton_template = "vroid"\n            log.info("SMPL requested, using vroid extraction + SMPL conversion")\n\n        # Validate model is provided\n        if skeleton_model is None:\n            raise RuntimeError(\n                "skeleton_model is required for UniRigExtractSkeletonNew. "\n                "Please connect a UniRigLoadSkeletonModel node."\n            )\n\n        # Validate model has checkpoint path\n        if not skeleton_model.get("checkpoint_path"):\n            raise RuntimeError(\n                "skeleton_model checkpoint not found. "\n                "Please connect a UniRigLoadSkeletonModel node."\n            )\n\n        log.info("Using pre-loaded cached model")\n\n        # Check if UniRig is available\n        if not os.path.exists(UNIRIG_PATH):\n            raise RuntimeError(\n                f"UniRig code not found at {UNIRIG_PATH}. "\n                "The lib/unirig directory should contain the UniRig source code."\n            )\n\n        # Create temp files\n        # ignore_cleanup_errors=True prevents Windows errors when npz files are still locked\n        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmpdir:\n            input_path = os.path.join(tmpdir, "input.glb")\n            npz_dir = os.path.join(tmpdir, "input")\n            npz_path = os.path.join(npz_dir, "raw_data.npz")\n\n            os.makedirs(npz_dir, exist_ok=True)\n\n            # Export mesh to GLB\n            step_start = time.time()\n            log.info("Exporting mesh to %s", input_path)\n            log.info(f"Mesh has {len(trimesh.vertices)} vertices, {len(trimesh.faces)} faces")\n            trimesh.export(input_path)\n            export_time = time.time() - step_start\n            log.info("Mesh exported in %.2fs", export_time)\n\n            # Step 1: Preprocess mesh using direct bpy import\n            step_start = time.time()\n            actual_face_count = target_face_count if target_face_count is not None else TARGET_FACE_COUNT\n            log.info("Using target face count: %s", actual_face_count)\n\n            direct_preprocess = _get_direct_preprocess()\n            if direct_preprocess is None:\n                raise RuntimeError(\n                    "Direct preprocessing module not available. "\n                    "Ensure bpy is installed: pip install bpy"\n                )\n\n            log.info("Step 1: Preprocessing mesh with direct bpy...")\n            direct_preprocess.preprocess_mesh(\n                input_file=input_path,\n                output_npz=npz_path,\n                target_face_count=actual_face_count\n            )\n\n            if not os.path.exists(npz_path):\n                raise RuntimeError(f"Preprocessing failed: {npz_path} not created")\n\n            preprocess_time = time.time() - step_start\n            log.info("[OK] Mesh preprocessed in %.2fs: %s", preprocess_time, npz_path)\n\n            # Step 2: Run skeleton inference\n            step_start = time.time()\n\n            # Map skeleton template to cls token\n            cls_value = None  # auto (let model decide)\n            if skeleton_template == "vroid" or skeleton_template == "mixamo":\n                cls_value = "vroid"  # Both need VRoid 52-bone skeleton with fingers\n            elif skeleton_template == "articulationxl":\n                cls_value = "articulationxl"\n\n            if cls_value:\n                log.info("Forcing skeleton template: %s", cls_value)\n            else:\n                log.info("Using auto skeleton detection")\n\n            # Run direct inference\n            direct_module = _get_direct_inference()\n            use_direct_subprocess = direct_module is None\n\n            if use_direct_subprocess:\n                log.info("Direct inference fallback: using UniRig env subprocess")\n            else:\n                log.info("Direct inference module available in ComfyUI runtime")\n\n            log.info("Step 2: Running skeleton inference...")\n\n            # Load raw_data.npz created by preprocessing\n            raw_data = np.load(npz_path)\n            mesh_vertices_raw = raw_data[\'vertices\']\n            mesh_faces_raw = raw_data[\'faces\']\n            raw_data.close()\n\n            # Get checkpoint path from skeleton_model\n            checkpoint_path = skeleton_model.get("checkpoint_path")\n            if not checkpoint_path:\n                checkpoint_path = os.path.join(UNIRIG_MODELS_DIR, "skeleton.safetensors")\n\n            if not os.path.exists(checkpoint_path):\n                raise RuntimeError(f"Skeleton checkpoint not found: {checkpoint_path}")\n\n            log.info("Using checkpoint: %s", checkpoint_path)\n\n            # Extract dtype and attn_backend from model config (set by UniRigLoadModel)\n            model_dtype = skeleton_model.get("dtype")\n            model_attn_backend = skeleton_model.get("attn_backend", "auto")\n\n            # Run direct skeleton prediction\n            if use_direct_subprocess:\n                direct_skeleton_result, norm_params = _run_direct_inference_subprocess(\n                    "skeleton",\n                    {\n                        "vertices": mesh_vertices_raw,\n                        "faces": mesh_faces_raw,\n                        "skeleton_checkpoint": checkpoint_path,\n                        "num_samples": 2048,\n                        "cls": cls_value or "articulationxl",\n                        "max_new_tokens": 2048,\n                        "seed": seed,\n                        "dtype": model_dtype,\n                        "attn_backend": model_attn_backend,\n                    },\n                )\n            else:\n                direct_skeleton_result, norm_params = direct_module.predict_skeleton_from_mesh(\n                    vertices=mesh_vertices_raw,\n                    faces=mesh_faces_raw,\n                    skeleton_checkpoint=checkpoint_path,\n                    num_samples=2048,\n                    cls=cls_value or "articulationxl",\n                    max_new_tokens=2048,\n                    seed=seed,\n                    dtype=model_dtype,\n                    attn_backend=model_attn_backend,\n                )\n\n            inference_time = time.time() - step_start\n\n            if direct_skeleton_result[\'joints\'] is None:\n                raise RuntimeError("Skeleton prediction failed - no joints generated")\n\n            num_joints = len(direct_skeleton_result[\'joints\'])\n            log.info("[OK] Inference completed in %.2fs", inference_time)\n            log.info("Generated %s joints", num_joints)\n\n            # Step 3: Process results\n            step_start = time.time()\n            log.info("Step 3: Processing inference results...")\n\n            # Extract skeleton data directly from model output\n            all_joints = direct_skeleton_result[\'joints\']\n            skeleton_bone_parents = direct_skeleton_result[\'parents\']\n            skeleton_bone_names = direct_skeleton_result.get(\'names\')\n            skeleton_bone_to_head = None  # Not needed - joints are already bone heads\n\n            # Create edges from parent relationships\n            edges = []\n            for i, parent in enumerate(skeleton_bone_parents):\n                if parent is not None and parent >= 0:\n                    edges.append([parent, i])\n\n            log.info(f"Results: {len(all_joints)} joints, {len(edges)} edges")\n\n            # Load preprocessing data\n            # For mesh/texture: always use raw_data.npz (has texture data)\n            # For skeleton: use parsed FBX output (has correct bone names from model)\n            preprocessing_npz = os.path.join(tmpdir, "input", "raw_data.npz")\n\n            uv_coords = None\n            uv_faces = None\n            material_name = None\n            texture_path = None\n            texture_data_base64 = None\n            texture_format = None\n            texture_width = 0\n            texture_height = 0\n\n            # Load mesh and texture data from preprocessing NPZ (raw_data.npz)\n            if os.path.exists(preprocessing_npz):\n                log.info("Loading mesh/texture from: raw_data.npz")\n                preprocess_data = np.load(preprocessing_npz, allow_pickle=True)\n\n                # Helper to safely get array field (handles 0-d arrays from None values)\n                def safe_get_array(key):\n                    if key not in preprocess_data:\n                        return None\n                    val = preprocess_data[key]\n                    if hasattr(val, \'ndim\') and val.ndim == 0:\n                        # 0-d array (scalar) - treat as None\n                        return None\n                    return val\n\n                mesh_vertices_original = preprocess_data[\'vertices\']\n                mesh_faces = preprocess_data[\'faces\']\n                vertex_normals = safe_get_array(\'vertex_normals\')\n                face_normals = safe_get_array(\'face_normals\')\n\n                # Load UV coordinates if available\n                uv_coords_data = safe_get_array(\'uv_coords\')\n                if uv_coords_data is not None and len(uv_coords_data) > 0:\n                    uv_coords = uv_coords_data\n                    uv_faces = safe_get_array(\'uv_faces\')\n                    log.info(f"Loaded UV coordinates: {len(uv_coords)} UVs")\n\n                # Load material and texture info if available\n                mat_name = safe_get_array(\'material_name\')\n                if mat_name is not None:\n                    material_name = str(mat_name)\n                tex_path = safe_get_array(\'texture_path\')\n                if tex_path is not None:\n                    texture_path = str(tex_path)\n\n                # Load texture data if available\n                # Note: texture fields may be 0-d string scalars, handle them specially\n                if \'texture_data_base64\' in preprocess_data:\n                    tex_data = preprocess_data[\'texture_data_base64\']\n                    # Handle both 0-d scalar and regular arrays\n                    if hasattr(tex_data, \'item\'):\n                        tex_str = tex_data.item() if tex_data.ndim == 0 else str(tex_data)\n                    else:\n                        tex_str = str(tex_data)\n\n                    if len(tex_str) > 0:\n                        texture_data_base64 = tex_str\n\n                        # Load texture metadata (also handle 0-d scalars)\n                        if \'texture_format\' in preprocess_data:\n                            fmt = preprocess_data[\'texture_format\']\n                            texture_format = fmt.item() if hasattr(fmt, \'item\') and fmt.ndim == 0 else str(fmt)\n                        if \'texture_width\' in preprocess_data:\n                            w = preprocess_data[\'texture_width\']\n                            texture_width = int(w.item() if hasattr(w, \'item\') and w.ndim == 0 else w)\n                        if \'texture_height\' in preprocess_data:\n                            h = preprocess_data[\'texture_height\']\n                            texture_height = int(h.item() if hasattr(h, \'item\') and h.ndim == 0 else h)\n\n                        log.info(f"Loaded texture: {texture_width}x{texture_height} {texture_format} ({len(texture_data_base64) // 1024}KB base64)")\n\n                # Close npz file to release handle (required for Windows temp cleanup)\n                preprocess_data.close()\n            else:\n                # Fallback: use trimesh data\n                mesh_vertices_original = np.array(trimesh.vertices, dtype=np.float32)\n                mesh_faces = np.array(trimesh.faces, dtype=np.int32)\n                vertex_normals = np.array(trimesh.vertex_normals, dtype=np.float32) if hasattr(trimesh, \'vertex_normals\') else None\n                face_normals = np.array(trimesh.face_normals, dtype=np.float32) if hasattr(trimesh, \'face_normals\') else None\n\n            # Normalize mesh to [-1, 1]\n            mesh_bounds_min = mesh_vertices_original.min(axis=0)\n            mesh_bounds_max = mesh_vertices_original.max(axis=0)\n            mesh_center = (mesh_bounds_min + mesh_bounds_max) / 2\n            mesh_extents = mesh_bounds_max - mesh_bounds_min\n            mesh_scale = mesh_extents.max() / 2\n\n            # Normalize mesh vertices to [-1, 1]\n            mesh_vertices = (mesh_vertices_original - mesh_center) / mesh_scale\n\n            log.info("Original mesh bounds: min=%s, max=%s", mesh_bounds_min, mesh_bounds_max)\n            log.info("Mesh scale: %.4f, extents: %s", mesh_scale, mesh_extents)\n            log.info(f"Normalized mesh bounds: min={mesh_vertices.min(axis=0)}, max={mesh_vertices.max(axis=0)}")\n\n            # Create trimesh object from normalized mesh data\n            normalized_mesh = Trimesh(\n                vertices=mesh_vertices,\n                faces=mesh_faces,\n                process=True\n            )\n            log.info(f"Created normalized mesh: {len(mesh_vertices)} vertices, {len(mesh_faces)} faces")\n\n            # Build parents list from bone_parents\n            if skeleton_bone_parents is not None:\n                bone_parents = skeleton_bone_parents\n                num_bones = len(bone_parents)\n                parents_list = [None if (p is None or p == -1) else int(p) for p in bone_parents]\n\n                # Get bone names from direct inference\n                if skeleton_bone_names is not None:\n                    if isinstance(skeleton_bone_names, np.ndarray):\n                        names_list = [str(name) for name in skeleton_bone_names]\n                    elif isinstance(skeleton_bone_names, list):\n                        names_list = [str(name) for name in skeleton_bone_names]\n                    else:\n                        names_list = [f"bone_{i}" for i in range(num_bones)]\n                    log.info(f"[OK] Using {len(names_list)} model-generated bone names")\n                    # Debug: show first few bone names to diagnose naming issues\n                    log.info(f"First 5 bone names: {names_list[:5]}")\n                else:\n                    names_list = [f"bone_{i}" for i in range(num_bones)]\n                    log.info(f"Using {len(names_list)} generic bone names (model returned no names)")\n\n                # Map bones to their head joint positions\n                if skeleton_bone_to_head is not None:\n                    bone_to_head = skeleton_bone_to_head\n                    bone_joints = np.array([all_joints[bone_to_head[i]] for i in range(num_bones)])\n                else:\n                    bone_joints = all_joints[:num_bones]\n\n                # Compute tails\n                tails = np.zeros((num_bones, 3))\n                for i in range(num_bones):\n                    children = [j for j, p in enumerate(parents_list) if p == i]\n                    if children:\n                        tails[i] = np.mean([bone_joints[c] for c in children], axis=0)\n                    else:\n                        if parents_list[i] is not None:\n                            direction = bone_joints[i] - bone_joints[parents_list[i]]\n                            tails[i] = bone_joints[i] + direction * 0.3\n                        else:\n                            tails[i] = bone_joints[i] + np.array([0, 0.1, 0])\n\n            else:\n                # No hierarchy - create simple chain\n                num_bones = len(all_joints)\n                bone_joints = all_joints\n                parents_list = [None] + list(range(num_bones-1))\n                names_list = [f"bone_{i}" for i in range(num_bones)]\n\n                tails = np.zeros_like(bone_joints)\n                for i in range(num_bones):\n                    children = [j for j, p in enumerate(parents_list) if p == i]\n                    if children:\n                        tails[i] = np.mean([bone_joints[c] for c in children], axis=0)\n                    else:\n                        if parents_list[i] is not None:\n                            direction = bone_joints[i] - bone_joints[parents_list[i]]\n                            tails[i] = bone_joints[i] + direction * 0.3\n                        else:\n                            tails[i] = bone_joints[i] + np.array([0, 0.1, 0])\n\n            # Remap bone names if mixamo was requested (applies to both branches above)\n            if remap_to_mixamo:\n                remapped_names = []\n                remapped_count = 0\n                for name in names_list:\n                    if name in VROID_TO_MIXAMO_BONE_MAP:\n                        remapped_names.append(VROID_TO_MIXAMO_BONE_MAP[name])\n                        remapped_count += 1\n                    else:\n                        remapped_names.append(name)  # Keep original if not in map\n                names_list = remapped_names\n                log.info(f"Remapped {remapped_count}/{len(names_list)} bones to Mixamo naming")\n                log.info(f"First 5 names after remap: {names_list[:5]}")\n\n            # Convert to SMPL skeleton if requested (filter 52 VRoid bones to 22 SMPL joints)\n            if remap_to_smpl:\n                log.info("Converting to SMPL skeleton (22 joints)...")\n\n                # Build VRoid name -> index mapping from current skeleton\n                vroid_name_to_idx = {name: i for i, name in enumerate(names_list)}\n\n                # Filter to only SMPL joints (22 out of 52)\n                smpl_joints = []\n                missing_joints = []\n\n                for smpl_name in SMPL_JOINT_NAMES:\n                    # Find corresponding VRoid bone name\n                    vroid_name = None\n                    for vn, sn in VROID_TO_SMPL_BONE_MAP.items():\n                        if sn == smpl_name:\n                            vroid_name = vn\n                            break\n\n                    if vroid_name and vroid_name in vroid_name_to_idx:\n                        idx = vroid_name_to_idx[vroid_name]\n                        smpl_joints.append(bone_joints[idx])\n                    else:\n                        missing_joints.append(smpl_name)\n                        # Use zero position as fallback (shouldn\'t happen)\n                        smpl_joints.append(np.array([0, 0, 0]))\n\n                if missing_joints:\n                    log.warning("Warning: Missing VRoid bones for SMPL joints: %s", missing_joints)\n\n                # Replace with SMPL data\n                bone_joints = np.array(smpl_joints)\n                names_list = list(SMPL_JOINT_NAMES)\n                parents_list = [None if p == -1 else p for p in SMPL_PARENTS]\n\n                # Compute tails using CANONICAL SMPL bone directions (for symmetric rest pose)\n                # This ensures left/right bones have mirrored orientations\n                num_smpl_joints = len(SMPL_JOINT_NAMES)\n                tails = np.zeros((num_smpl_joints, 3))\n\n                for i, joint_name in enumerate(SMPL_JOINT_NAMES):\n                    # Get canonical bone direction\n                    direction = np.array(SMPL_BONE_DIRECTIONS.get(joint_name, [0, 1, 0]))\n\n                    # Compute bone length from child distance or use default\n                    children = [j for j, p in enumerate(parents_list) if p == i]\n                    if children:\n                        # Use distance to first child as bone length\n                        child_idx = children[0]\n                        bone_length = np.linalg.norm(bone_joints[child_idx] - bone_joints[i])\n                        if bone_length < 0.01:\n                            bone_length = SMPL_DEFAULT_BONE_LENGTH\n                    else:\n                        # Leaf bone - use default length\n                        bone_length = SMPL_DEFAULT_BONE_LENGTH\n\n                    # Tail = head + direction * length\n                    tails[i] = bone_joints[i] + direction * bone_length\n\n                log.info(f"Converted to SMPL: {len(names_list)} joints with canonical bone orientations")\n\n                # === STEP 1: Detect current facing direction and rotate to SMPL standard ===\n                # SMPL standard (before Y-up conversion): facing -Y, lateral along X, up along Z\n                # We need to detect current orientation and rotate to match\n\n                # Get shoulder positions to determine lateral axis\n                l_shoulder_idx = names_list.index(\'L_Shoulder\')\n                r_shoulder_idx = names_list.index(\'R_Shoulder\')\n                pelvis_idx = names_list.index(\'Pelvis\')\n                head_idx = names_list.index(\'Head\') if \'Head\' in names_list else names_list.index(\'Neck\')\n\n                l_shoulder = bone_joints[l_shoulder_idx]\n                r_shoulder = bone_joints[r_shoulder_idx]\n                pelvis = bone_joints[pelvis_idx]\n                head = bone_joints[head_idx]\n\n                # Compute current orientation vectors\n                shoulder_vec = r_shoulder - l_shoulder  # Left to Right\n                spine_vec = head - pelvis  # Up direction\n\n                # Normalize\n                shoulder_vec = shoulder_vec / (np.linalg.norm(shoulder_vec) + 1e-8)\n                spine_vec = spine_vec / (np.linalg.norm(spine_vec) + 1e-8)\n\n                # Forward = cross(right, up) for right-handed system\n                forward_vec = np.cross(shoulder_vec, spine_vec)\n                forward_vec = forward_vec / (np.linalg.norm(forward_vec) + 1e-8)\n\n                log.info("Current orientation - Lateral: %s, Up: %s, Forward: %s", shoulder_vec, spine_vec, forward_vec)\n\n                # Determine which axis is lateral (should be X for SMPL)\n                # In Blender Z-up, SMPL standard is: lateral=X, up=Z, forward=-Y\n                lateral_axis = np.argmax(np.abs(shoulder_vec))\n                up_axis = np.argmax(np.abs(spine_vec))\n\n                # Check if we need to rotate around Z axis to align lateral with X\n                if lateral_axis == 0:\n                    # Already aligned with X\n                    log.info("Lateral axis already aligned with X")\n                    z_rotation_angle = 0\n                elif lateral_axis == 1:\n                    # Lateral is along Y, need to rotate 90 degrees around Z\n                    z_rotation_angle = np.pi / 2 if shoulder_vec[1] > 0 else -np.pi / 2\n                    log.info(f"Rotating {np.degrees(z_rotation_angle):.0f} degrees around Z to align lateral with X")\n                else:\n                    # Lateral is along Z (our current case), need to rotate around up axis\n                    # This shouldn\'t happen in Z-up Blender coords, but handle it\n                    z_rotation_angle = 0\n                    log.info("Unusual: Lateral along Z axis")\n\n                # For the current mesh: lateral is along Y (in original coords), up is along Z\n                # After Z-up to Y-up conversion, this becomes: lateral along Y, up along Y - wrong!\n                # We need to rotate so lateral is along X before the conversion\n\n                # Actually, let\'s detect more carefully:\n                # If shoulders differ mainly in Y, we need 90 degree rotation around Z\n                if abs(shoulder_vec[1]) > abs(shoulder_vec[0]) and abs(shoulder_vec[1]) > 0.5:\n                    # Lateral is along Y, rotate 90 degrees around Z\n                    cos_a, sin_a = 0, 1  # 90 degrees\n                    if shoulder_vec[1] < 0:\n                        sin_a = -1  # -90 degrees\n\n                    def rotate_around_z(points):\n                        """Rotate points 90 degrees around Z axis"""\n                        rotated = np.zeros_like(points)\n                        rotated[..., 0] = cos_a * points[..., 0] - sin_a * points[..., 1]\n                        rotated[..., 1] = sin_a * points[..., 0] + cos_a * points[..., 1]\n                        rotated[..., 2] = points[..., 2]\n                        return rotated\n\n                    log.info("Rotating 90 degrees around Z to align shoulders with X axis")\n                    bone_joints = rotate_around_z(bone_joints)\n                    tails = rotate_around_z(tails)\n                    mesh_vertices = rotate_around_z(mesh_vertices)\n                    vertex_normals = rotate_around_z(vertex_normals)\n                    face_normals = rotate_around_z(face_normals)\n\n                # === STEP 2: Rotate from Blender Z-up to SMPL Y-up ===\n                # This is a -90 degree rotation around X axis: (x, y, z) -> (x, z, -y)\n                # SMPL uses: X=right, Y=up, Z=back\n                # Blender uses: X=right, Y=forward, Z=up\n                def rotate_to_smpl_coords(points):\n                    """Rotate points from Blender coords (Z-up) to SMPL coords (Y-up)"""\n                    rotated = np.zeros_like(points)\n                    rotated[..., 0] = points[..., 0]   # X stays X\n                    rotated[..., 1] = points[..., 2]   # Z becomes Y (up)\n                    rotated[..., 2] = -points[..., 1]  # -Y becomes Z (back)\n                    return rotated\n\n                # Rotate joints, tails, mesh vertices, and normals\n                bone_joints = rotate_to_smpl_coords(bone_joints)\n                tails = rotate_to_smpl_coords(tails)\n                mesh_vertices = rotate_to_smpl_coords(mesh_vertices)\n                vertex_normals = rotate_to_smpl_coords(vertex_normals)\n                face_normals = rotate_to_smpl_coords(face_normals)\n\n                # === STEP 3: Ensure correct handedness (L_Shoulder at +X, R_Shoulder at -X) ===\n                # After rotation, check if left/right are correct\n                l_shoulder_new = bone_joints[l_shoulder_idx]\n                r_shoulder_new = bone_joints[r_shoulder_idx]\n\n                # In SMPL, L_Shoulder should have positive X, R_Shoulder negative X\n                if l_shoulder_new[0] < r_shoulder_new[0]:\n                    # Left/Right are swapped, need to mirror along X\n                    log.info("Mirroring along X to fix left/right")\n                    bone_joints[..., 0] = -bone_joints[..., 0]\n                    tails[..., 0] = -tails[..., 0]\n                    mesh_vertices[..., 0] = -mesh_vertices[..., 0]\n                    vertex_normals[..., 0] = -vertex_normals[..., 0]\n                    face_normals[..., 0] = -face_normals[..., 0]\n                    # Also need to flip face winding\n                    mesh_faces = mesh_faces[:, ::-1]\n\n                # Update mesh bounds after rotation\n                mesh_bounds_min = mesh_vertices.min(axis=0)\n                mesh_bounds_max = mesh_vertices.max(axis=0)\n                mesh_center = (mesh_bounds_min + mesh_bounds_max) / 2\n\n                log.info("Rotated to SMPL Y-up coordinate system")\n\n            # Save as RawData NPZ for skinning phase\n            persistent_npz = os.path.join(folder_paths.get_temp_directory(), f"skeleton_{seed}.npz")\n            np.savez(\n                persistent_npz,\n                vertices=mesh_vertices,\n                vertex_normals=vertex_normals,\n                faces=mesh_faces,\n                face_normals=face_normals,\n                joints=bone_joints,\n                tails=tails,\n                parents=np.array(parents_list, dtype=object),\n                names=np.array(names_list, dtype=object),\n                uv_coords=uv_coords if uv_coords is not None else np.array([], dtype=np.float32),\n                uv_faces=uv_faces if uv_faces is not None else np.array([], dtype=np.int32),\n                material_name=material_name if material_name else "",\n                texture_path=texture_path if texture_path else "",\n                mesh_bounds_min=mesh_bounds_min,\n                mesh_bounds_max=mesh_bounds_max,\n                mesh_center=mesh_center,\n                mesh_scale=mesh_scale,\n                skin=None,\n                no_skin=None,\n                matrix_local=None,\n                path=None,\n                cls=cls_value\n            )\n            log.info("Saved skeleton NPZ to: %s", persistent_npz)\n\n            # Build skeleton dict with ALL data\n            skeleton = {\n                "vertices": all_joints,\n                "edges": edges,\n                "joints": bone_joints,\n                "tails": tails,\n                "names": names_list,\n                "parents": parents_list,\n                "mesh_vertices": mesh_vertices,\n                "mesh_faces": mesh_faces,\n                "mesh_vertex_normals": vertex_normals,\n                "mesh_face_normals": face_normals,\n                "uv_coords": uv_coords,\n                "uv_faces": uv_faces,\n                "material_name": material_name,\n                "texture_path": texture_path,\n                "texture_data_base64": texture_data_base64,\n                "texture_format": texture_format,\n                "texture_width": texture_width,\n                "texture_height": texture_height,\n                "mesh_bounds_min": mesh_bounds_min,\n                "mesh_bounds_max": mesh_bounds_max,\n                "mesh_center": mesh_center,\n                "mesh_scale": mesh_scale,\n                "is_normalized": True,\n                "skeleton_npz_path": persistent_npz,\n                "bone_names": names_list,\n                "bone_parents": parents_list,\n                "output_format": original_template,\n            }\n\n            if skeleton_bone_to_head is not None:\n                skeleton[\'bone_to_head_vertex\'] = skeleton_bone_to_head.tolist()\n\n            # Note: skeleton_data NPZ file was already closed immediately after extraction\n            # to avoid Windows file locking issues during temp cleanup\n\n            log.info(f"Included hierarchy: {len(names_list)} bones with parent relationships")\n\n            # Create texture preview output\n            if texture_data_base64:\n                texture_preview, tex_w, tex_h = decode_texture_to_comfy_image(texture_data_base64)\n                if texture_preview is not None:\n                    log.info("Texture preview created: %sx%s", tex_w, tex_h)\n                else:\n                    log.warning("Warning: Could not decode texture for preview")\n                    texture_preview = create_placeholder_texture()\n            else:\n                log.info("No texture available for preview")\n                texture_preview = create_placeholder_texture()\n\n            total_time = time.time() - total_start\n            log.info("Skeleton extraction complete!")\n            log.info("TOTAL TIME: %.2fs", total_time)\n            return (normalized_mesh, skeleton, texture_preview)\n'
    if current == desired:
        log("skeleton_extraction.py autonomous patch already present")
        return
    backup = target.with_suffix(".py.autonomous_backup")
    if not backup.exists():
        backup.write_text(current, encoding="utf-8")
    target.write_text(desired, encoding="utf-8")
    log("skeleton_extraction.py autonomous patch applied")

def build_install_script(cfg: InstallerConfig) -> str:
    python_path = normalize_path(cfg.python_path)
    comfyui_path = normalize_path(cfg.comfyui_path)
    unirig_path = normalize_path(cfg.unirig_path)
    target_version = get_target_comfy_env_version(cfg.env_mode)
    env_mode = (cfg.env_mode or "local").lower()

    return f'''$ErrorActionPreference = 'Stop'

$python = "{python_path}"
$comfyui = "{comfyui_path}"
$unirig = "{unirig_path}"
$targetComfyEnv = "{target_version}"

function Write-Step($msg) {{
    Write-Host ""
    Write-Host "==== $msg ====" -ForegroundColor Cyan
}}

function Write-Warn($msg) {{
    Write-Host "WARNING: $msg" -ForegroundColor Yellow
}}

function Fail($msg) {{
    Write-Host ""
    Write-Host "ERROR: $msg" -ForegroundColor Red
    exit 1
}}

Write-Step "Validation"

if (-not (Test-Path $python)) {{
    Fail "Python not found: $python"
}}

if (-not (Test-Path $comfyui)) {{
    Fail "ComfyUI path not found: $comfyui"
}}

if (-not (Test-Path $unirig)) {{
    Fail "UniRig path not found: $unirig"
}}

$mainPy = Join-Path $comfyui "main.py"
if (-not (Test-Path $mainPy)) {{
    Fail "Invalid ComfyUI folder: main.py not found"
}}

Write-Step "Update comfy-env"
& $python -m pip install --upgrade "comfy-env==$targetComfyEnv"
if ($LASTEXITCODE -ne 0) {{
    Fail "Failed to update comfy-env"
}}

# Portable/embedded preview support (mandatory diagnostic):
# UniRig prestartup imports comfy_3d_viewers before the isolated UniRig env is active.
# Therefore the viewer package must exist in the MAIN ComfyUI Python for Portable/embedded builds.
Write-Step "Check 3D preview support"
Write-Host "Environment mode: {env_mode}"
Write-Host "Python used for preview support: $python"
$pythonLower = $python.ToLowerInvariant()
$looksEmbedded = ($pythonLower -like "*python_embeded*" -or $pythonLower -like "*python_embedded*")
$shouldInstallViewer = ("{env_mode}" -eq "embedded" -or "{env_mode}" -eq "portable" -or $looksEmbedded)

& $python -c "import comfy_3d_viewers; print('comfy_3d_viewers import OK')" 2>$null
if ($LASTEXITCODE -eq 0) {{
    Write-Host "comfy_3d_viewers already available in this Python."
}} else {{
    Write-Warn "comfy_3d_viewers is missing in this Python."
    if ($shouldInstallViewer) {{
        Write-Host "Installing comfy-3d-viewers into the selected Portable/embedded Python..."
        & $python -m pip install --upgrade comfy-3d-viewers
        if ($LASTEXITCODE -ne 0) {{
            Write-Warn "Failed to install comfy-3d-viewers. UniRig may still run, but the integrated 3D preview may remain unavailable."
        }} else {{
            & $python -c "import comfy_3d_viewers; print('comfy_3d_viewers verification OK')"
            if ($LASTEXITCODE -ne 0) {{
                Write-Warn "comfy_3d_viewers installed but import verification failed. Preview may remain unavailable until ComfyUI is restarted."
            }} else {{
                Write-Host "Portable 3D viewer support installed and verified."
            }}
        }}
    }} else {{
        Write-Host "Preview package install skipped: environment is not Portable/embedded."
    }}
}}

Write-Step "Clean old UniRig environments"
$nodesDir = Join-Path $unirig "nodes"
if (Test-Path $nodesDir) {{
    $oldEnvs = Get-ChildItem -LiteralPath $nodesDir -Force | Where-Object {{ $_.Name -like "_env_*" }}
    if ($oldEnvs.Count -gt 0) {{
        foreach ($envItem in $oldEnvs) {{
            Write-Host "Removing: $($envItem.FullName)"
            Remove-Item -LiteralPath $envItem.FullName -Recurse -Force -ErrorAction Stop
        }}
    }} else {{
        Write-Host "No old UniRig environment found."
    }}
}} else {{
    Write-Warn "nodes folder not found. Cleanup skipped."
}}

Write-Step "Install UniRig environment"
Set-Location $unirig

$pythonDir = Split-Path $python -Parent
$comfyEnvExe1 = Join-Path $pythonDir "Scripts\\comfy-env.exe"
$comfyEnvExe2 = Join-Path $pythonDir "Scripts\\comfy-env"

if (Test-Path $comfyEnvExe1) {{
    Write-Host "Using: $comfyEnvExe1 install"
    & $comfyEnvExe1 install
    if ($LASTEXITCODE -ne 0) {{
        Fail "comfy-env install failed via executable"
    }}
}} elseif (Test-Path $comfyEnvExe2) {{
    Write-Host "Using: $comfyEnvExe2 install"
    & $comfyEnvExe2 install
    if ($LASTEXITCODE -ne 0) {{
        Fail "comfy-env install failed via executable"
    }}
}} else {{
    Write-Host "Using fallback: python -m comfy_env.cli install"
    & $python -m comfy_env.cli install
    if ($LASTEXITCODE -ne 0) {{
        if ("{env_mode}" -eq "embedded") {{
            Write-Host "Legacy fallback: python -m comfy_env install"
            & $python -m comfy_env install
            if ($LASTEXITCODE -ne 0) {{
                Fail "comfy-env install failed via cli and legacy fallback"
            }}
        }} else {{
            Fail "comfy-env install failed via cli"
        }}
    }}
}}

Write-Step "Patch mesh_io.py"
$patchScript = @'
from pathlib import Path
import sys

unirig = Path(r"{unirig_path}")
mesh = unirig / "nodes" / "mesh_io.py"

if not mesh.exists():
    print("mesh_io.py not found, patch skipped")
    sys.exit(0)

content = mesh.read_text(encoding="utf-8")

old_block = """"file_path": (mesh_files, {{
                    "tooltip": "Mesh file to load. Refresh the node after changing source_folder."
                }}),"""

new_block = """"file_path": ("STRING", {{
                    "default": "3d/test.glb",
                    "multiline": False,
                    "tooltip": "Relative or absolute mesh path."
                }}),"""

if new_block in content:
    print("mesh_io.py already patched")
    sys.exit(0)

if old_block not in content:
    print("Patch block not found in mesh_io.py")
    sys.exit(0)

backup = mesh.with_suffix(".py.pre_patch_backup")
if not backup.exists():
    backup.write_text(content, encoding="utf-8")

mesh.write_text(content.replace(old_block, new_block), encoding="utf-8")
print("mesh_io.py patched")
'@

& $python -c $patchScript
if ($LASTEXITCODE -ne 0) {{
    Fail "mesh_io.py patch failed"
}}

Write-Step "Done"
Write-Host "UniRig installation script completed." -ForegroundColor Green
Write-Host "You can now reopen ComfyUI and test a UniRig workflow." -ForegroundColor Green
'''

class ConfirmDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, message, yes_text, no_text):
        super().__init__(parent)
        self.result = False
        self.title(title)
        self.geometry("540x228")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.transient(parent)
        self.grab_set()

        card = ctk.CTkFrame(self, fg_color=CARD, corner_radius=18, border_width=1, border_color=BORDER)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True)

        inner = ctk.CTkFrame(content, fg_color="transparent")
        inner.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            inner,
            text=message,
            justify="center",
            wraplength=470,
            font=ctk.CTkFont(size=14),
            text_color=TEXT,
        ).pack(anchor="center", padx=24, pady=(6, 18))

        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack()
        ctk.CTkButton(btns, text=yes_text, fg_color=BLUE, hover_color=BLUE_HOVER, corner_radius=12, font=ctk.CTkFont(size=13, weight="bold"), command=self.on_yes).pack(side="left", padx=(0, 8))
        ctk.CTkButton(btns, text=no_text, fg_color="#E9EEF6", text_color=TEXT, hover_color="#DDE5F1", corner_radius=12, font=ctk.CTkFont(size=13, weight="bold"), command=self.on_no).pack(side="left")
        self.protocol("WM_DELETE_WINDOW", self.on_no)

    def on_yes(self):
        self.result = True
        self.destroy()

    def on_no(self):
        self.result = False
        self.destroy()



class InfoDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, message, close_text="OK"):
        super().__init__(parent)
        self.title(title)
        self.geometry("620x430")
        self.resizable(False, False)
        self.configure(fg_color=BG)
        self.transient(parent)
        self.grab_set()

        card = ctk.CTkFrame(self, fg_color=CARD, corner_radius=18, border_width=1, border_color=BORDER)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        title_lbl = ctk.CTkLabel(card, text=title, text_color=TITLE, font=ctk.CTkFont(size=20, weight="bold"))
        title_lbl.pack(anchor="w", padx=20, pady=(18, 8))

        text_box = ctk.CTkTextbox(
            card,
            fg_color="#FFFFFF",
            border_width=1,
            border_color="#D4DCE8",
            corner_radius=14,
            text_color=TEXT,
            font=ctk.CTkFont(size=12),
            activate_scrollbars=True,
            wrap="word",
        )
        text_box.pack(fill="both", expand=True, padx=20, pady=(0, 14))
        text_box.insert("1.0", message)
        text_box.configure(state="disabled")

        btn = ctk.CTkButton(
            card,
            text=close_text,
            width=84,
            height=34,
            corner_radius=11,
            fg_color=PURPLE_TINT,
            hover_color=PURPLE_TINT_HOVER,
            text_color=TEXT,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.destroy,
        )
        btn.pack(anchor="e", padx=20, pady=(0, 18))


class SectionHeader(ctk.CTkFrame):
    def __init__(self, master, number: str):
        super().__init__(master, fg_color="transparent")
        self.badge = ctk.CTkLabel(
            self,
            text=number,
            width=28,
            height=28,
            corner_radius=14,
            fg_color="#E9EEF5",
            text_color=TITLE,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.badge.pack(side="left")
        self.title = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=17, weight="bold"), text_color=SECTION)
        self.title.pack(side="left", padx=(12, 0), pady=(0, 1))


class StatusCell(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="#F6F8FC", corner_radius=12, border_width=1, border_color="#C5D0DE", height=50)
        self.pack_propagate(False)

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="both", expand=True, padx=12, pady=8)

        self.top = ctk.CTkLabel(row, text="", anchor="w", text_color=TEXT, font=ctk.CTkFont(size=12, weight="bold"))
        self.top.pack(side="left", fill="x", expand=True)

        self.bottom = ctk.CTkLabel(row, text="", anchor="e", text_color=MUTED, font=ctk.CTkFont(size=11))
        self.bottom.pack(side="right", padx=(8, 0))

    def set(self, title, title_color=TEXT, subtitle="", subtitle_color=MUTED):
        self.top.configure(text=title, text_color=title_color)
        self.bottom.configure(text=subtitle, text_color=subtitle_color)


class ToolRow(ctk.CTkFrame):
    def __init__(self, master, icon_text: str):
        super().__init__(master, fg_color=CARD_SOFT, corner_radius=14, border_width=1, border_color=BORDER, height=58)
        self.pack_propagate(False)

        self.icon_box = ctk.CTkFrame(self, fg_color="#EFF3F8", corner_radius=10, width=34, height=34)
        self.icon_box.pack(side="left", padx=(12, 10), pady=12)
        self.icon_box.pack_propagate(False)
        self.icon = ctk.CTkLabel(self.icon_box, text=icon_text, text_color="#4B5D78", font=ctk.CTkFont(size=16))
        self.icon.place(relx=0.5, rely=0.5, anchor="center")

        self.text_row = ctk.CTkFrame(self, fg_color="transparent")
        self.text_row.pack(side="left", fill="x", expand=True, padx=(0, 8), pady=10)
        self.title = ctk.CTkLabel(self.text_row, text="", text_color=TEXT, font=ctk.CTkFont(size=13, weight="bold"), anchor="w")
        self.title.pack(side="left")
        self.dot = ctk.CTkLabel(self.text_row, text="·", text_color="#8FA0B8", font=ctk.CTkFont(size=14))
        self.dot.pack(side="left", padx=8)
        self.desc = ctk.CTkLabel(self.text_row, text="", text_color=MUTED, font=ctk.CTkFont(size=11), anchor="w")
        self.desc.pack(side="left")

        self.btn = ctk.CTkButton(
            self,
            text="",
            width=92,
            height=34,
            corner_radius=11,
            fg_color="#EEF2F7",
            hover_color="#E3E9F1",
            border_width=1,
            border_color="#D0D8E4",
            text_color=TEXT,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.btn.pack(side="right", padx=(8, 12), pady=12)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1360x790")
        self.minsize(1180, 740)
        self.configure(fg_color=BG)

        self.lang = ctk.StringVar(value="FR")
        self.cfg = InstallerConfig()
        self.comfy_var = ctk.StringVar()
        self.unirig_var = ctk.StringVar()
        self.python_var = ctk.StringVar()
        self.current_action = ctk.StringVar()
        self.progress_text = ctk.StringVar()
        self.log_queue = queue.Queue()
        self.install_running = False
        self.script_cache = ""
        self.detected_old_envs = []
        self.analysis_has_run = False
        self.last_env_python = ""
        self.install_succeeded = False
        self.local_desktop_guidance_shown = False
        self.logo_image = None
        self.global_status_state = ""
        self.global_status_key = ""
        self.current_action_key = ""

        self._load_config()
        self._build_ui()
        self.apply_language()
        self.after(100, self.flush_logs)

    def on_language_change(self, _=None):
        value = self.lang.get().lower()
        if value in LANGS:
            self.lang.set(value.upper())
        self.apply_language()

    def tr(self, key):
        return LANGS[self.lang.get().lower()][key]

    def _render_header_title(self):
        title = self.tr("title")
        self.header_canvas.delete("all")

        pad_left = 0
        # V10 polish: optical vertical centering with the official logo.
        visual_baseline = 45
        title_descent = int(self.header_title_font.metrics("descent"))
        title_y = visual_baseline + title_descent

        # Brand title: keep "OneClick Installer" highlighted, matching the public visual identity.
        prefix = "UniRig "
        accent = "OneClick Installer"
        if title.startswith(prefix):
            self.header_canvas.create_text(
                pad_left,
                title_y,
                text=prefix,
                anchor="sw",
                fill=TITLE,
                font=self.header_title_font,
            )
            prefix_width = self.header_title_font.measure(prefix)
            self.header_canvas.create_text(
                pad_left + prefix_width,
                title_y,
                text=accent,
                anchor="sw",
                fill=BLUE,
                font=self.header_title_font,
            )
            total_width = pad_left + prefix_width + self.header_title_font.measure(accent) + 4
        else:
            self.header_canvas.create_text(
                pad_left,
                title_y,
                text=title,
                anchor="sw",
                fill=TITLE,
                font=self.header_title_font,
            )
            total_width = pad_left + self.header_title_font.measure(title) + 4
        self.header_canvas.configure(width=total_width)

    def _card(self, master, height: int):
        frame = ctk.CTkFrame(master, fg_color=CARD, corner_radius=22, border_width=1, border_color=BORDER, height=height)
        frame.pack_propagate(False)
        return frame

    def _build_ui(self):
        shell = ctk.CTkFrame(self, fg_color=SHELL, corner_radius=0)
        shell.pack(fill="both", expand=True, padx=56, pady=(12, 36))

        root = ctk.CTkFrame(shell, fg_color="transparent")
        root.pack(fill="both", expand=True, padx=16, pady=(10, 0))

        header = ctk.CTkFrame(root, fg_color="transparent", height=62)
        header.pack(fill="x", pady=(0, 8))
        header.pack_propagate(False)

        left = ctk.CTkFrame(header, fg_color="transparent")
        left.pack(side="left", anchor="w")
        try:
            import base64
            import io
            from PIL import Image

            # Tkinter PhotoImage is kept only for the native window icon.
            # CustomTkinter labels should receive CTkImage to avoid HighDPI warnings.
            self.logo_tk_image = tk.PhotoImage(data=APP_ICON_PNG_B64, format="png")
            self.iconphoto(True, self.logo_tk_image)

            logo_pil = Image.open(io.BytesIO(base64.b64decode(APP_ICON_PNG_B64))).convert("RGBA")
            # Best-effort native Windows icon for taskbar / Alt-Tab when launched from source or EXE.
            try:
                temp_icon_path = Path(os.environ.get("TEMP", ".")) / "unirig_oneclick_icon.ico"
                logo_pil.save(temp_icon_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (256, 256)])
                self.iconbitmap(str(temp_icon_path))
            except Exception:
                pass
            self.logo_image = ctk.CTkImage(
                light_image=logo_pil,
                dark_image=logo_pil,
                size=(56, 56),
            )
            self.logo_label = ctk.CTkLabel(left, image=self.logo_image, text="", width=56, height=56)
            self.logo_label.pack(side="left", padx=(0, 16), pady=(4, 0))
        except Exception:
            self.logo_label = None
        self.header_canvas = tk.Canvas(left, height=62, highlightthickness=0, bd=0, bg=SHELL)
        self.header_canvas.pack(side="left", anchor="w")
        self.header_title_font = tkfont.Font(family="Segoe UI", size=31, weight="bold")
        self.header_subtitle_font = tkfont.Font(family="Segoe UI", size=13, weight="bold")

        right = ctk.CTkFrame(header, fg_color="transparent")
        right.pack(side="right", anchor="e", pady=(2, 0))
        self.info_btn = ctk.CTkButton(
            right,
            text="",
            width=74,
            height=38,
            corner_radius=11,
            fg_color="#EEF2F7",
            hover_color="#E1E8F1",
            border_width=1,
            border_color="#CFD8E6",
            text_color=TEXT,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self.show_info,
        )
        self.info_btn.pack(side="right", padx=(10, 0))
        self.lang_menu = ctk.CTkOptionMenu(
            right,
            variable=self.lang,
            values=["FR", "EN", "CN"],
            width=54,
            height=38,
            corner_radius=11,
            fg_color="#EEF2F7",
            button_color="#E5EBF4",
            button_hover_color="#DCE5F0",
            text_color=TEXT,
            dropdown_fg_color="#FFFFFF",
            dropdown_hover_color="#EDF3FF",
            dropdown_text_color=TEXT,
            command=self.on_language_change,
        )
        self.lang_menu.pack(side="right")

        content = ctk.CTkFrame(root, fg_color="transparent")
        content.pack(fill="both", expand=True)
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)

        TOP_H = 332
        BOTTOM_H = 274

        self.config_card = self._card(content, TOP_H)
        self.config_card.grid(row=0, column=0, padx=(0, 4), pady=(0, 8), sticky="ew")
        self.analysis_card = self._card(content, TOP_H)
        self.analysis_card.grid(row=0, column=1, padx=(4, 0), pady=(0, 8), sticky="ew")
        self.journal_card = self._card(content, BOTTOM_H)
        self.journal_card.grid(row=1, column=0, padx=(0, 4), sticky="ew")
        self.advanced_card = self._card(content, BOTTOM_H)
        self.advanced_card.grid(row=1, column=1, padx=(4, 0), sticky="ew")

        self._build_config_card()
        self._build_analysis_card()
        self._build_journal_card()
        self._build_advanced_card()

        self.footer_label = ctk.CTkLabel(
            root,
            text=APP_FOOTER,
            text_color=MUTED,
            font=ctk.CTkFont(size=11),
        )
        self.footer_label.pack(fill="x", pady=(8, 0))

    def _build_config_card(self):
        head = ctk.CTkFrame(self.config_card, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(12, 6))
        self.config_head = SectionHeader(head, "1")
        self.config_head.pack(anchor="w")

        comfy_head = ctk.CTkFrame(self.config_card, fg_color="transparent")
        comfy_head.pack(fill="x", padx=18)
        self.comfy_lbl = ctk.CTkLabel(comfy_head, text="", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT)
        self.comfy_lbl.pack(side="left")
        self.helper_lbl = ctk.CTkLabel(comfy_head, text="", font=ctk.CTkFont(size=10), text_color=MUTED)
        self.helper_lbl.pack(side="left", padx=(12, 0), pady=(1, 0))

        comfy_row = ctk.CTkFrame(self.config_card, fg_color="transparent")
        comfy_row.pack(fill="x", padx=18, pady=(3, 6))
        self.comfy_entry = ctk.CTkEntry(comfy_row, textvariable=self.comfy_var, height=36, corner_radius=12, border_width=1, fg_color="#FFFFFF", border_color="#D6DEEA", text_color=TEXT, font=ctk.CTkFont(size=13))
        self.comfy_entry.pack(side="left", fill="x", expand=True)
        self.browse_comfy_btn = ctk.CTkButton(comfy_row, text="", width=82, height=36, corner_radius=12, fg_color=PURPLE_TINT, hover_color=PURPLE_TINT_HOVER, text_color=TEXT, border_width=1, border_color="#D0C0F4", font=ctk.CTkFont(size=12, weight="bold"), command=self.browse_comfy)
        self.browse_comfy_btn.pack(side="left", padx=(12, 0))

        self.unirig_lbl = ctk.CTkLabel(self.config_card, text="", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT)
        self.unirig_lbl.pack(anchor="w", padx=18, pady=(0, 0))

        unirig_row = ctk.CTkFrame(self.config_card, fg_color="transparent")
        unirig_row.pack(fill="x", padx=18, pady=(3, 5))
        self.unirig_entry = ctk.CTkEntry(unirig_row, textvariable=self.unirig_var, height=36, corner_radius=12, border_width=1, fg_color="#FFFFFF", border_color="#D6DEEA", text_color=TEXT, font=ctk.CTkFont(size=13))
        self.unirig_entry.pack(side="left", fill="x", expand=True)
        self.browse_unirig_btn = ctk.CTkButton(unirig_row, text="", width=82, height=36, corner_radius=12, fg_color=PURPLE_TINT, hover_color=PURPLE_TINT_HOVER, text_color=TEXT, border_width=1, border_color="#D0C0F4", font=ctk.CTkFont(size=12, weight="bold"), command=self.browse_unirig)
        self.browse_unirig_btn.pack(side="left", padx=(12, 0))

        self.python_lbl = ctk.CTkLabel(self.config_card, text="", font=ctk.CTkFont(size=12, weight="bold"), text_color=TEXT)
        self.python_lbl.pack(anchor="w", padx=18, pady=(0, 0))

        python_row = ctk.CTkFrame(self.config_card, fg_color="transparent")
        python_row.pack(fill="x", padx=18, pady=(3, 6))
        self.python_entry = ctk.CTkEntry(python_row, textvariable=self.python_var, height=34, corner_radius=12, border_width=1, fg_color="#FFFFFF", border_color="#D6DEEA", text_color=TEXT, font=ctk.CTkFont(size=13))
        self.python_entry.pack(side="left", fill="x", expand=True)
        self.browse_python_btn = ctk.CTkButton(python_row, text="", width=82, height=34, corner_radius=12, fg_color=PURPLE_TINT, hover_color=PURPLE_TINT_HOVER, text_color=TEXT, border_width=1, border_color="#D0C0F4", font=ctk.CTkFont(size=12, weight="bold"), command=self.browse_python)
        self.browse_python_btn.pack(side="left", padx=(12, 0))

        actions_row = ctk.CTkFrame(self.config_card, fg_color="transparent")
        actions_row.pack(anchor="w", padx=18, pady=(8, 4))
        self.detect_btn = ctk.CTkButton(actions_row, text="", width=94, height=34, corner_radius=12, fg_color=PURPLE_TINT, hover_color=PURPLE_TINT_HOVER, text_color=TEXT, border_width=1, border_color="#D0C0F4", font=ctk.CTkFont(size=12, weight="bold"), command=self.detect_with_feedback)
        self.detect_btn.pack(side="left")
        self.install_unirig_btn = ctk.CTkButton(actions_row, text="", width=120, height=34, corner_radius=12, fg_color="#EEF2F7", hover_color="#E3E9F1", text_color=TEXT, border_width=1, border_color="#D0D8E4", font=ctk.CTkFont(size=12, weight="bold"), command=self.install_unirig_node)
        self.install_unirig_btn.pack(side="left", padx=(8, 0))

    def _build_analysis_card(self):
        top = ctk.CTkFrame(self.analysis_card, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 6))
        self.analysis_head = SectionHeader(top, "2")
        self.analysis_head.pack(side="left")
        self.analysis_done = ctk.CTkLabel(top, text="", text_color=GREEN_TXT, font=ctk.CTkFont(size=12, weight="bold"))
        self.analysis_done.pack(side="left", padx=(18, 0), pady=(3, 0))

        status_grid = ctk.CTkFrame(self.analysis_card, fg_color="transparent")
        status_grid.pack(fill="x", padx=16, pady=(26, 0))
        status_grid.grid_columnconfigure(0, weight=1)
        status_grid.grid_columnconfigure(1, weight=1)

        self.status_comfy = StatusCell(status_grid)
        self.status_comfy.grid(row=0, column=0, padx=(0, 7), pady=(0, 7), sticky="ew")
        self.status_python = StatusCell(status_grid)
        self.status_python.grid(row=0, column=1, padx=(7, 0), pady=(0, 7), sticky="ew")
        self.status_env = StatusCell(status_grid)
        self.status_env.grid(row=1, column=0, padx=(0, 7), pady=(0, 7), sticky="ew")
        self.status_old = StatusCell(status_grid)
        self.status_old.grid(row=1, column=1, padx=(7, 0), pady=(0, 7), sticky="ew")

        action_wrap = ctk.CTkFrame(self.analysis_card, fg_color="transparent")
        action_wrap.pack(fill="both", expand=True, padx=16, pady=(2, 10))
        self.next_step_label = ctk.CTkLabel(action_wrap, text="", text_color="#314C8F", font=ctk.CTkFont(size=12, weight="bold"), justify="center", wraplength=430)
        self.next_step_label.pack_forget()
        action_center = ctk.CTkFrame(action_wrap, fg_color="transparent")
        action_center.place(relx=0.5, rely=0.60, anchor="center")
        self.oneclick_btn = ctk.CTkButton(action_center, text="", width=250, height=48, corner_radius=15, fg_color=ONECLICK, hover_color=ONECLICK_HOVER, text_color="#2B2025", border_width=1, border_color="#E4BFCB", font=ctk.CTkFont(size=17, weight="bold"), command=self.run_oneclick)
        self.oneclick_btn.pack(anchor="center", pady=(0, 7))
        self.progress_holder = ctk.CTkFrame(action_center, fg_color="transparent", height=36)
        self.progress_holder.pack(anchor="center")
        self.progress_holder.pack_propagate(False)
        self.progressbar = ctk.CTkProgressBar(self.progress_holder, width=250, height=10, corner_radius=999, progress_color=BLUE, fg_color="#CAD2DE")
        self.progressbar.pack(anchor="center", pady=(0, 6))
        self.progressbar.set(0)
        self.progress_label = ctk.CTkLabel(self.progress_holder, textvariable=self.progress_text, text_color=MUTED, font=ctk.CTkFont(size=11))
        self.progress_label.pack(anchor="center")
        self.progress_visible = False
        self._hide_progress_widgets()

    def _build_journal_card(self):
        header = ctk.CTkFrame(self.journal_card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 6))
        self.journal_head = SectionHeader(header, "3")
        self.journal_head.pack(side="left")
        self.clear_btn = ctk.CTkButton(header, text="", width=90, height=32, corner_radius=12, fg_color=PURPLE_TINT, hover_color=PURPLE_TINT_HOVER, text_color=TEXT, border_width=1, border_color="#D0C0F4", font=ctk.CTkFont(size=12, weight="bold"), command=self.clear_log)
        self.clear_btn.pack(side="right", pady=(2, 0))
        self.save_btn = ctk.CTkButton(header, text="", width=112, height=32, corner_radius=12, fg_color="#EEF2F7", hover_color="#E3E9F1", text_color=TEXT, border_width=1, border_color="#D0D8E4", font=ctk.CTkFont(size=12, weight="bold"), command=self.save_log)
        self.save_btn.pack(side="right", padx=(0, 8), pady=(2, 0))

        current_row = ctk.CTkFrame(self.journal_card, fg_color="transparent")
        current_row.pack(fill="x", padx=18)
        self.current_action_lbl = ctk.CTkLabel(current_row, text="", text_color=TEXT, font=ctk.CTkFont(size=12, weight="bold"))
        self.current_action_lbl.pack(side="left")
        self.current_action_val = ctk.CTkLabel(current_row, textvariable=self.current_action, text_color=MUTED, font=ctk.CTkFont(size=12))
        self.current_action_val.pack(side="left", padx=(8, 0))

        log_wrap = ctk.CTkFrame(self.journal_card, fg_color="transparent")
        log_wrap.pack(fill="both", expand=True, padx=18, pady=(8, 14))
        log_wrap.grid_columnconfigure(0, weight=1)
        log_wrap.grid_rowconfigure(0, weight=1)

        self.log_box = ctk.CTkTextbox(log_wrap, corner_radius=14, border_width=1, border_color="#C8D0DB", fg_color=JOURNAL_BG, text_color="#223047", activate_scrollbars=False, font=ctk.CTkFont(size=12))
        self.log_box.grid(row=0, column=0, sticky="nsew")
        self.log_scroll = ctk.CTkScrollbar(log_wrap, orientation="vertical", width=9, button_color="#C9D2DE", button_hover_color="#AEBACB", fg_color="transparent", corner_radius=999, command=self.log_box.yview)
        self.log_scroll.grid(row=0, column=1, sticky="ns", padx=(6, 0))
        self.log_box.configure(yscrollcommand=self.log_scroll.set)

    def _build_advanced_card(self):
        header = ctk.CTkFrame(self.advanced_card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 6))
        self.advanced_head = SectionHeader(header, "4")
        self.advanced_head.pack(anchor="w")

        # V7 UI polish: keep only the two export cards and center them vertically
        # inside the available space of block 4.
        body = ctk.CTkFrame(self.advanced_card, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        rows = ctk.CTkFrame(body, fg_color="transparent")
        rows.place(relx=0.5, rely=0.5, anchor="center", relwidth=1.0)

        self.script_card = ToolRow(rows, "📄")
        self.script_card.pack(fill="x", pady=(0, 8))
        self.json_card = ToolRow(rows, "🗂")
        self.json_card.pack(fill="x", pady=(0, 0))

        self.advanced_hint_icon = None
        self.advanced_hint = None

    def apply_language(self):
        self.title(APP_NAME)
        self._render_header_title()
        self.config_head.title.configure(text=self.tr("configuration"))
        self.analysis_head.title.configure(text=self.tr("analysis"))
        self.journal_head.title.configure(text=self.tr("journal"))
        self.advanced_head.title.configure(text=self.tr("advanced"))
        self.info_btn.configure(text=self.tr("info"))

        self.comfy_lbl.configure(text=self.tr("comfy_path"))
        self.unirig_lbl.configure(text=self.tr("unirig_path"))
        self.python_lbl.configure(text=self.tr("python_path"))
        self.browse_comfy_btn.configure(text=self.tr("browse"))
        self.browse_unirig_btn.configure(text=self.tr("browse"))
        self.browse_python_btn.configure(text=self.tr("browse"))
        self.helper_lbl.configure(text=self.tr("helper"))
        self.detect_btn.configure(text=self.tr("analyze"))
        self.install_unirig_btn.configure(text=self.tr("install_unirig_btn"))
        self.current_action_lbl.configure(text=self.tr("current_action"))
        self.clear_btn.configure(text=self.tr("clear"))
        self.save_btn.configure(text=self.tr("save"))
        self.oneclick_btn.configure(text=self.tr("oneclick"))

        self.script_card.title.configure(text=self.tr("export_script"))
        self.script_card.desc.configure(text=self.tr("export_script_desc"))
        self.script_card.btn.configure(text=self.tr("export"), command=self.export_script)
        self.json_card.title.configure(text=self.tr("export_json"))
        self.json_card.desc.configure(text=self.tr("export_json_desc"))
        self.json_card.btn.configure(text=self.tr("export"), command=self.export_json)
        if self.advanced_hint is not None:
            self.advanced_hint.configure(text=self.tr("advanced_hint"))

        self._refresh_statuses_default()
        if self.current_action_key:
            self.current_action.set(self.tr(self.current_action_key))
        elif not self.current_action.get():
            self.current_action_key = "not_started"
            self.current_action.set(self.tr("not_started"))
        if self.install_running:
            if not self.progress_text.get():
                self.progress_text.set(self.tr("progress_running"))
            self._show_progress_widgets()
        else:
            self._hide_progress_widgets()
        if self.log_box.get("1.0", "end-1c").strip() == "":
            self.log_box.insert("1.0", self.tr("log_placeholder"))
        self._save_config()

    def _refresh_statuses_default(self):
        if self.analysis_has_run:
            self.status_comfy.set(
                "✔ " + self.tr("detected_comfy"),
                GREEN_TXT if self.cfg.comfyui_path else RED_TXT,
            )
            if self.cfg.python_path:
                python_text = self.cfg.python_version or self.tr("version_unknown")
                self.status_python.set("✔ " + self.tr("detected_python") + f" : {python_text}", GREEN_TXT)
            else:
                self.status_python.set("✖ " + self.tr("status_missing"), RED_TXT)
            if self.cfg.comfy_env_version:
                self.status_env.set("✔ " + self.tr("detected_env") + f" : {self.cfg.comfy_env_version}", GREEN_TXT)
            else:
                self.status_env.set("✖ " + self.tr("status_missing"), RED_TXT)
            if self.install_succeeded:
                self.status_old.set("✔ " + self.tr("env_ready"), GREEN_TXT)
            elif self.cfg.unirig_path:
                self.status_old.set("✔ " + self.tr("unirig_installed"), GREEN_TXT)
            elif self.detected_old_envs:
                self.status_old.set("• " + self.tr("detected_old"), ORANGE_TXT)
            else:
                self.status_old.set("✖ " + self.tr("no_unirig_env"), RED_TXT)
            if self.global_status_key:
                self.set_global_status(self.global_status_state or "ok", self.tr(self.global_status_key), self.global_status_key)
            elif not self.analysis_done.cget("text"):
                self.set_global_status("ok", self.tr("analysis_done"), "analysis_done")
        else:
            # V9.1 polish: before the user runs Analyse, status cards stay visually neutral.
            # Detection labels are shown only after an actual analysis pass.
            self.status_comfy.set("", TEXT)
            self.status_python.set("", TEXT)
            self.status_env.set("", TEXT)
            self.status_old.set("", TEXT)
            self.analysis_done.configure(text="")

    def _show_progress_widgets(self):
        self.progressbar.configure(progress_color=BLUE, fg_color="#CAD2DE")
        self.progress_label.configure(text_color=MUTED)
        self.progress_visible = True

    def _hide_progress_widgets(self):
        self.progressbar.stop()
        self.progressbar.set(0)
        self.progressbar.configure(progress_color=CARD, fg_color=CARD)
        self.progress_label.configure(text_color=CARD)
        self.progress_text.set("")
        self.progress_visible = False

    def set_global_status(self, state: str, text: str, key: str = ""):
        color = GREEN_TXT if state == "ok" else ORANGE_TXT if state == "warning" else RED_TXT
        self.global_status_state = state
        if key:
            self.global_status_key = key
        self.analysis_done.configure(text="●  " + text, text_color=color)

    def find_unirig_env_python(self, extra_paths=None):
        search_paths = []
        if extra_paths:
            search_paths.extend(extra_paths)
        if self.last_env_python:
            search_paths.append(self.last_env_python)
        return find_unirig_env_python_from_path(self.cfg.unirig_path, search_paths)

    def post_install_check(self, extra_paths=None):
        env_python = self.find_unirig_env_python(extra_paths)
        if not env_python:
            self.log("ERROR: Post-install check failed: UniRig env python not found")
            return False, ["env_python"], ""
        self.last_env_python = env_python
        self.log(f"Post-install env python: {env_python}")
        checks = [
            ("bpy", "import bpy"),
            ("torch_cluster", "import torch_cluster"),
            ("torch_scatter", "import torch_scatter"),
            ("cumm", "import cumm"),
            ("spconv", "import spconv"),
            ("flash_attn", "import flash_attn"),
        ]
        missing = []
        for name, code in checks:
            result = subprocess.run(
                [env_python, "-c", code],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if result.returncode == 0:
                self.log(f"[post-check] {name}: OK")
            else:
                self.log(f"[post-check] {name}: MISSING")
                missing.append(name)
        return len(missing) == 0, missing, env_python

    def fallback_install_missing(self, env_python, missing):
        if env_python:
            self.last_env_python = env_python
        self.log("=== FALLBACK INSTALL (missing modules) ===")
        log_recovery_matrix_policy(self.log, "Fallback policy: reuse the embedded-validated recovery matrix inside the UniRig isolated env")
        urls = {
            "torch_scatter": "https://github.com/PozzettiAndrea/cuda-wheels/releases/download/torch_scatter-latest/torch_scatter-2.1.2%2Bcu128torch2.8-cp311-cp311-win_amd64.whl",
            "torch_cluster": "https://github.com/PozzettiAndrea/cuda-wheels/releases/download/torch_cluster-latest/torch_cluster-1.6.3%2Bcu128torch2.8-cp311-cp311-win_amd64.whl",
            "flash_attn": "https://github.com/mjun0812/flash-attention-prebuild-wheels/releases/download/v0.4.10/flash_attn-2.7.4+cu128torch2.8-cp311-cp311-win_amd64.whl",
        }

        for name in missing:
            if name in urls:
                url = urls[name]
                attempts = 3 if name == "flash_attn" else 1
                last_stdout = ""
                last_stderr = ""
                success = False
                for attempt in range(1, attempts + 1):
                    if attempts > 1:
                        self.log(f"[fallback] installing {name} (attempt {attempt}/{attempts}) from {url}")
                    else:
                        self.log(f"[fallback] installing {name} from {url}")
                    pip_cmd = [env_python, "-m", "pip", "install", url]
                    if name == "flash_attn":
                        pip_cmd = [env_python, "-m", "pip", "install", "--timeout", "1200", "--retries", "3", "--disable-pip-version-check", url]
                    result = subprocess.run(
                        pip_cmd,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        check=False,
                    )
                    stdout = (result.stdout or "").strip()
                    stderr = (result.stderr or "").strip()
                    last_stdout = stdout
                    last_stderr = stderr
                    if result.returncode == 0:
                        success = True
                        break
                    timeout_like = ("ReadTimeoutError" in stderr or "Read timed out" in stderr or "The read operation timed out" in stderr)
                    if name == "flash_attn" and timeout_like and attempt < attempts:
                        self.log("[fallback] flash_attn download timed out, retrying...")
                        continue
                    break
                if success:
                    self.log(f"[fallback] {name}: OK")
                else:
                    self.log(f"[fallback] {name}: FAILED")
                    if name == "flash_attn":
                        self.log("[fallback] flash_attn could not be downloaded after multiple attempts. Check your internet connection, then relaunch OneClick Install.")
                    if last_stdout:
                        for line in last_stdout.splitlines()[-10:]:
                            self.log(line)
                    if last_stderr:
                        for line in last_stderr.splitlines()[-10:]:
                            self.log(line)
                continue

            if name in ["cumm", "spconv"]:
                self.log(f"[fallback] preparing clean install for {name} via cu128 extra index")
                uninstall_targets = ["cumm", "cumm-cu128", "spconv", "spconv-cu128"]
                uninstall_result = subprocess.run(
                    [env_python, "-m", "pip", "uninstall", "-y", *uninstall_targets],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=False,
                )
                uninstall_stdout = (uninstall_result.stdout or "").strip()
                uninstall_stderr = (uninstall_result.stderr or "").strip()
                if uninstall_stdout:
                    for line in uninstall_stdout.splitlines()[-8:]:
                        self.log(line)
                if uninstall_stderr:
                    for line in uninstall_stderr.splitlines()[-8:]:
                        self.log(line)

                install_cmd = [
                    env_python,
                    "-m",
                    "pip",
                    "install",
                    "cumm-cu128",
                    "spconv-cu128",
                    "--extra-index-url",
                    "https://ratharog.github.io/cumm-spconv/",
                ]
                self.log("[fallback] installing cumm-cu128 and spconv-cu128 from extra index")
                result = subprocess.run(
                    install_cmd,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=False,
                )
                stdout = (result.stdout or "").strip()
                stderr = (result.stderr or "").strip()
                if result.returncode == 0:
                    self.log(f"[fallback] {name}: OK")
                else:
                    self.log(f"[fallback] {name}: FAILED")
                    if stdout:
                        for line in stdout.splitlines()[-12:]:
                            self.log(line)
                    if stderr:
                        for line in stderr.splitlines()[-12:]:
                            self.log(line)

    def set_progress_state(self, text_key, running):
        if running:
            self.progress_text.set(self.tr(text_key))
            self._show_progress_widgets()
            self.progressbar.start()
        else:
            if text_key == "progress_idle":
                self._hide_progress_widgets()
            else:
                self.progress_text.set(self.tr(text_key))
                self._show_progress_widgets()
                self.progressbar.stop()
                self.progressbar.set(0)

    def _copy_text_to_clipboard(self, text: str):
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update()
        except Exception:
            pass

    def browse_comfy(self):
        chosen = filedialog.askdirectory(initialdir=self.comfy_var.get() or None)
        if chosen:
            self.comfy_var.set(chosen)

    def browse_unirig(self):
        chosen = filedialog.askdirectory(initialdir=self.unirig_var.get() or None)
        if chosen:
            self.unirig_var.set(chosen)

    def browse_python(self):
        initial_dir = None
        current_value = self.python_var.get().strip()
        if current_value:
            current_path = Path(current_value)
            initial_dir = str(current_path.parent if current_path.suffix else current_path)

        chosen_dir = filedialog.askdirectory(initialdir=initial_dir or None)
        if not chosen_dir:
            return

        chosen_path = Path(chosen_dir)
        candidates = [
            chosen_path / "python.exe",
            chosen_path / "pythonw.exe",
            chosen_path / "Scripts" / "python.exe",
            chosen_path / "python_embeded" / "python.exe",
            chosen_path / "venv" / "Scripts" / "python.exe",
        ]
        found = next((candidate for candidate in candidates if candidate.exists()), None)

        if found is None:
            for pattern in ("python*.exe", "**/python.exe", "**/pythonw.exe"):
                matches = [m for m in chosen_path.glob(pattern) if m.is_file()]
                if matches:
                    found = matches[0]
                    break

        final_value = str(found if found is not None else chosen_path)
        self.python_var.set(final_value)
        self.cfg.python_path = final_value

    def detect_with_feedback(self):
        self.current_action_key = "analysis_running"
        self.current_action.set(self.tr("analysis_running"))
        self.log(self.tr("analysis_running"))
        self.detect_btn.configure(state="disabled")
        self.update_idletasks()
        self.after(50, self._detect_with_feedback_async)

    def _detect_with_feedback_async(self):
        try:
            self.detect()
        finally:
            self.detect_btn.configure(state="normal")

    def detect(self):
        try:
            data = detect_environment(self.comfy_var.get(), self.python_var.get(), self.unirig_var.get())
            self.cfg.comfyui_path = data["comfyui_path"]
            self.cfg.python_path = data["python_path"]
            self.python_var.set(data["python_path"] or "")
            self.cfg.python_version = data["python_version"]
            self.cfg.comfy_env_version = data["comfy_env_version"]
            self.cfg.custom_nodes_path = data["custom_nodes_path"]
            self.cfg.env_mode = data["env_mode"]
            self.cfg.unirig_path = data["unirig_path"]
            self.unirig_var.set(data["unirig_path"] or "")
            self.detected_old_envs = detect_old_unirig_env(self.cfg.unirig_path)
            self.analysis_has_run = True
            self.install_succeeded = False

            error = False
            warning = False
            message = ""
            message_key = ""
            main_py_ok = (Path(self.cfg.comfyui_path) / "main.py").exists()
            torch_version = ""
            if self.cfg.python_path:
                try:
                    torch_version = safe_run_capture([self.cfg.python_path, "-c", "import torch; print(torch.__version__)"])
                except Exception:
                    torch_version = ""

            if not main_py_ok:
                error = True
                message = "Selected ComfyUI folder is invalid (main.py not found)."
            elif not self.cfg.python_path:
                error = True
                message = "Python not detected"
            elif (self.cfg.python_version or "").startswith("3.13"):
                error = True
                message = "Python 3.13 is not supported. Please use Python 3.12."
            elif not self.cfg.unirig_path:
                error = True
                message = "UniRig not found in this ComfyUI"
            elif torch_version.startswith("2.8"):
                warning = True
                message = "Environment ready (Torch 2.8 warning)"
            elif self.detected_old_envs:
                warning = True
                message_key = "detected_old"
                message = self.tr(message_key)
            else:
                message_key = "install_ready_config"
                message = self.tr(message_key)

            if main_py_ok:
                self.status_comfy.set("✔ " + self.tr("detected_comfy"), GREEN_TXT)
            else:
                self.status_comfy.set("✖ Invalid ComfyUI folder", RED_TXT)

            if self.cfg.python_path:
                python_color = GREEN_TXT
                if (self.cfg.python_version or "").startswith("3.13"):
                    python_color = RED_TXT
                self.status_python.set("✔ " + self.tr("detected_python") + f" : {self.cfg.python_version or self.tr('version_unknown')}", python_color)
            else:
                self.status_python.set("✖ " + self.tr("status_missing"), RED_TXT)

            if self.cfg.comfy_env_version:
                self.status_env.set("✔ " + self.tr("detected_env") + f" : {self.cfg.comfy_env_version}", GREEN_TXT)
            else:
                self.status_env.set("✖ " + self.tr("status_missing"), RED_TXT)

            if self.install_succeeded:
                self.status_old.set("✔ " + self.tr("env_ready"), GREEN_TXT)
            elif self.cfg.unirig_path:
                self.status_old.set("✔ " + self.tr("unirig_installed"), GREEN_TXT)
            elif self.detected_old_envs:
                self.status_old.set("• " + self.tr("detected_old"), ORANGE_TXT)
            else:
                self.status_old.set("✖ " + self.tr("no_unirig_env"), RED_TXT)

            if error:
                self.set_global_status("error", message, message_key)
                self.oneclick_btn.configure(state="disabled")
            elif warning:
                self.set_global_status("warning", message, message_key)
                self.oneclick_btn.configure(state="normal")
            else:
                self.set_global_status("ok", message, message_key)
                self.oneclick_btn.configure(state="normal")

            self.current_action_key = message_key
            self.current_action.set(message)
            self._write_detection_log()
            # V8.3: always log Portable/embedded 3D preview package state during Analyse.
            self._ensure_3d_preview_support(install=False)
            self._save_config()
            self._apply_install_unirig_button_policy()
            # Desktop Local guidance is shown only when the user clicks Installer UniRig.

        except Exception as e:
            self.current_action.set(str(e))
            self.log(str(e))

    def _write_detection_log(self):
        self.log(f"{self.tr('comfy_path_found')} : {self.cfg.comfyui_path}")
        if self.cfg.python_path:
            self.log(self.tr("python_found"))
        else:
            self.log(self.tr("python_not_found"))
        if self.cfg.comfy_env_version:
            self.log(self.tr("comfy_env_found"))
        else:
            self.log(self.tr("comfy_env_missing"))
        if self.cfg.unirig_path:
            self.log(f"{self.tr('unirig_path_set')} : {self.cfg.unirig_path}")
            self.log(self.tr("env_detected"))
            self.log(self.tr("unirig_synced"))
        else:
            self.log("⚠ " + self.tr("unirig_missing"))
        if self.cfg.python_path:
            self.log(f"{self.tr('python_path_set')} : {self.cfg.python_path}")
        if self.cfg.custom_nodes_path:
            self.log(f"{self.tr('custom_nodes_path_set')} : {self.cfg.custom_nodes_path}")
        self.log(f"{self.tr('env_type_found')} : {self.cfg.env_mode or 'local'}")
        self.log(self.tr("detect_done"))
        if self.cfg.python_path:
            try:
                torch_version = safe_run_capture([self.cfg.python_path, "-c", "import torch; print(torch.__version__)"])
                if torch_version:
                    self.log(f"Version PyTorch détectée : {torch_version}")
                    if torch_version.startswith("2.8"):
                        self.log("⚠ WARNING: Torch 2.8 detected. This configuration may produce incomplete UniRig environments (missing torch_cluster / flash_attn).")
            except Exception:
                pass


    def _is_local_desktop_mode(self) -> bool:
        return (self.cfg.env_mode or "local").lower() == "local"

    def _local_desktop_manager_guidance_message(self) -> str:
        return (
            "Configuration Desktop Local détectée.\n\n"
            "Étapes recommandées :\n\n"
            "1. Cliquez sur Installer UniRig\n"
            "2. Cliquez sur OneClick Install\n"
            "3. Ouvrez ComfyUI\n"
            "4. Lancez un workflow\n\n"
            "UniRig est prêt à être utilisé."
        )

    def _show_local_desktop_manager_guidance(self, *, force: bool = False):
        if not self._is_local_desktop_mode():
            return
        if not force and self.local_desktop_guidance_shown:
            return
        self.local_desktop_guidance_shown = True
        msg = self._local_desktop_manager_guidance_message()
        self.log("Mode Desktop Local détecté.")
        self.log("Procédure : Installer UniRig → OneClick Install → ouvrir ComfyUI → lancer un workflow.")
        messagebox.showinfo("Desktop Local - installation UniRig", msg, parent=self)

    def _apply_install_unirig_button_policy(self):
        try:
            label = "Installer UniRig" if self._is_local_desktop_mode() else self.tr("install_unirig_btn")
            self.install_unirig_btn.configure(
                state="normal",
                text=label,
                fg_color="#EEF2F7",
                hover_color="#E3E9F1",
                text_color=TEXT,
            )
        except Exception:
            pass

    def _is_embedded_or_portable_env(self):
        mode = (getattr(self.cfg, "env_mode", "") or "").lower()
        python_path = (self.python_var.get() or getattr(self.cfg, "python_path", "") or "").lower()
        comfy_path = (self.comfy_var.get() or getattr(self.cfg, "comfyui_path", "") or "").lower()
        return (
            mode == "embedded"
            or "python_embeded" in python_path
            or "python_embedded" in python_path
            or "windows_portable" in comfy_path
        )

    def _run_import_check(self, python_path, module_name):
        try:
            result = subprocess.run(
                [python_path, "-c", f"import {module_name}; print('OK')"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            return result.returncode == 0, (result.stdout or "") + (result.stderr or "")
        except Exception as e:
            return False, str(e)

    def _is_comfyui_running_for_current_path(self) -> bool:
        """Best-effort Windows process check for the selected ComfyUI path."""
        try:
            comfy_path = (self.comfy_var.get() or getattr(self.cfg, "comfyui_path", "") or "").strip()
            if not comfy_path:
                return False
            needle = str(Path(comfy_path).resolve()).lower()
            if os.name != "nt":
                return False

            ps_cmd = (
                "Get-CimInstance Win32_Process | "
                "Where-Object { $_.CommandLine -and ($_.Name -match 'python|comfy') } | "
                "Select-Object -ExpandProperty CommandLine"
            )
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=8,
            )
            output = (proc.stdout or "").lower()
            if not output:
                return False
            for line in output.splitlines():
                if needle in line and "unirig_oneclick" not in line and "unirig_installer" not in line:
                    return True
        except Exception:
            return False
        return False

    def _warn_if_comfyui_running(self) -> None:
        """Show a short warning only if ComfyUI seems to be running."""
        if self._is_comfyui_running_for_current_path():
            try:
                messagebox.showwarning(self.tr("comfy_running_title"), self.tr("comfy_running_msg"), parent=self)
            except Exception:
                pass

    def _ensure_3d_preview_support(self, install=False):
        """Check/install comfy_3d_viewers in Portable/embedded main Python."""
        self.log("Check 3D preview support")

        if not self._is_embedded_or_portable_env():
            self.log("3D preview support check skipped: not Portable/embedded")
            return True

        python_path = (self.python_var.get() or getattr(self.cfg, "python_path", "") or "").strip()
        if not python_path or not Path(python_path).exists():
            self.log("⚠ 3D preview check skipped: Python path not found")
            return False

        ok, details = self._run_import_check(python_path, "comfy_3d_viewers")
        if ok:
            self.log("✔ comfy_3d_viewers already available")
            return True

        self.log("⚠ comfy_3d_viewers missing in Portable/embedded Python")
        if not install:
            self.log("ℹ It will be installed after Install UniRig or during OneClick Install")
            return False

        self.log("Installing comfy-3d-viewers into Portable/embedded Python...")
        cmd = [python_path, "-m", "pip", "install", "--upgrade", "--disable-pip-version-check", "comfy-3d-viewers"]
        self.log("$ " + " ".join(cmd))
        try:
            proc = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=600,
            )
            combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
            for line in combined.splitlines()[-30:]:
                if line.strip():
                    self.log("[3d-viewer] " + line.strip())
            if proc.returncode != 0:
                self.log("⚠ comfy-3d-viewers installation failed")
                return False
        except Exception as e:
            self.log(f"⚠ comfy-3d-viewers installation failed: {e}")
            return False

        ok, details = self._run_import_check(python_path, "comfy_3d_viewers")
        if ok:
            self.log("✔ comfy_3d_viewers installed and verified")
            return True

        self.log("⚠ comfy_3d_viewers installed but import verification failed")
        if details:
            for line in details.splitlines()[-10:]:
                if line.strip():
                    self.log("[3d-viewer-check] " + line.strip())
        return False

    def install_unirig_node(self):
        if self.install_running:
            return
        # V10.2: do not show the old Desktop Local guidance popup here.
        # The README and final admin popup now provide the user-facing flow.
        self._warn_if_comfyui_running()
        try:
            self.install_unirig_btn.configure(text=self.tr("button_working"), state="disabled")
            self.detect_btn.configure(state="disabled")
            self.update_idletasks()
        except Exception:
            pass
        threading.Thread(target=self._install_unirig_node_worker, daemon=True).start()

    def _install_unirig_node_worker(self):
        import tempfile
        import urllib.request
        import zipfile

        unirig_repo = ("ComfyUI-UniRig", "https://github.com/PozzettiAndrea/ComfyUI-UniRig.git", "https://codeload.github.com/PozzettiAndrea/ComfyUI-UniRig/zip/refs/heads/main")
        # V8 multi-config policy: this button installs UniRig ONLY.
        # Env-Manager / CameraPack / heavy dependencies are not installed here.
        # The OneClick Install step builds the isolated UniRig environment and
        # installs everything required for runtime.
        repos = [unirig_repo]
        try:
            self.after(0, lambda: self.install_unirig_btn.configure(state="disabled"))
            self.after(0, lambda: self.detect_btn.configure(state="disabled"))
            self.current_action_key = "install_unirig_running"
            self.current_action.set(self.tr("install_unirig_running"))
            self.log(self.tr("install_unirig_running"))

            comfy_path = Path(self.comfy_var.get().strip())
            if not comfy_path.exists():
                raise RuntimeError(self.tr("comfy_path_missing"))

            detected = detect_environment(
                str(comfy_path),
                manual_python_path=self.python_var.get().strip(),
                manual_unirig_path="",
            )
            custom_nodes = Path(detected.get("custom_nodes_path") or (comfy_path / "custom_nodes"))
            custom_nodes.mkdir(parents=True, exist_ok=True)
            self.log(f"Install target custom_nodes: {custom_nodes}")
            self.log("Installation UniRig seule : les dépendances seront gérées par OneClick Install.")

            installed_any = False
            unirig_target = custom_nodes / "ComfyUI-UniRig"
            unirig_alt = custom_nodes / "comfyui-unirig"

            for folder_name, repo_url, zip_url in repos:
                target = custom_nodes / folder_name
                if target.exists():
                    self.log(f"✔ {folder_name} installé")
                    continue
                try:
                    self.log(f"Cloning {folder_name} from: {repo_url}")
                    subprocess.run(["git", "clone", repo_url, str(target)], check=True, capture_output=True, text=True)
                except Exception as git_error:
                    self.log(f"Git clone unavailable or failed for {folder_name}, trying ZIP download: {git_error}")
                    with tempfile.TemporaryDirectory() as td:
                        zip_path = Path(td) / f"{folder_name}.zip"
                        urllib.request.urlretrieve(zip_url, zip_path)
                        with zipfile.ZipFile(zip_path, 'r') as zf:
                            zf.extractall(td)
                        extracted = None
                        for x in Path(td).iterdir():
                            if x.is_dir() and x.name != '__MACOSX':
                                extracted = x
                                break
                        if extracted is None:
                            raise RuntimeError(f"Downloaded archive for {folder_name} does not contain expected root folder")
                        shutil.copytree(extracted, target)
                self.log(f"✔ {folder_name} installé")
                installed_any = True

            unirig_existing = unirig_target if unirig_target.exists() else (unirig_alt if unirig_alt.exists() else None)
            if unirig_existing:
                self.unirig_var.set(str(unirig_existing))
                self.cfg.unirig_path = str(unirig_existing)

            if not installed_any:
                self.log(self.tr("install_unirig_exists"))

            # V8.3: Portable/embedded needs comfy_3d_viewers in the main Python for UniRig preview.
            self._ensure_3d_preview_support(install=True)

            self.log("→ Installation UniRig terminée")
            self.log("UniRig installé. Vous pouvez maintenant lancer OneClick Install.")
            self.after(0, lambda: messagebox.showinfo(
                APP_NAME,
                "UniRig has been installed.\nNext step: click on OneClick Install.",
                parent=self
            ))
            self.current_action_key = "install_unirig_done"
            self.current_action.set(self.tr("install_unirig_done"))
            self.after(0, self.detect_with_feedback)
        except Exception as e:
            self.log(f"{self.tr('install_unirig_failed')}: {e}")
            self.current_action_key = "install_unirig_failed"
            self.current_action.set(self.tr("install_unirig_failed"))
            self.after(0, lambda: messagebox.showerror(
                APP_NAME,
                f"{self.tr('install_unirig_failed')}\n\n{e}",
                parent=self
            ))
        finally:
            self.after(0, self._apply_install_unirig_button_policy)
            self.after(0, lambda: self.detect_btn.configure(state="normal"))

    def show_info(self):
        dialog = InfoDialog(self, self.tr("about_title"), self.tr("about_body"))
        self.wait_window(dialog)

    def _ask_oneclick_authorization(self):
        lang = self.lang.get().lower()
        if lang == "fr":
            title = "Autorisation OneClick Install"
            message = "D'anciens environnements ont été détectés\net peuvent gêner la bonne installation de UniRig dans ComfyUI.\nVoulez-vous les écraser (recommandé) ?"
            yes_text = "Oui"
            no_text = "Non"
        elif lang == "cn":
            title = "一键安装授权"
            message = "检测到旧的 UniRig 环境，\n它们可能会影响在 ComfyUI 中正确安装 UniRig。\n是否覆盖它们（推荐）？"
            yes_text = "是"
            no_text = "否"
        else:
            title = "OneClick Install authorization"
            message = "Existing UniRig environments were detected\nand may interfere with a proper UniRig installation in ComfyUI.\nDo you want to overwrite them (recommended)?"
            yes_text = "Yes"
            no_text = "No"

        result = []
        dialog = ConfirmDialog(self, title, message, yes_text, no_text)
        self.wait_window(dialog)
        result.append(dialog.result)
        return bool(result and result[0])

    def _ask_cleanup(self):
        dialog = ConfirmDialog(self, self.tr("popup_title"), self.tr("popup_msg"), self.tr("popup_yes"), self.tr("popup_no"))
        self.wait_window(dialog)
        return bool(dialog.result)

    def run_oneclick(self):
        if self.install_running:
            return
        if not self.analysis_has_run:
            self.detect()
        if not self.analysis_has_run or not self.cfg.comfyui_path or not self.cfg.python_path:
            self.current_action_key = "analysis_required"
            self.current_action.set(self.tr("analysis_required"))
            self.log(self.tr("analysis_required"))
            return

        try:
            self.oneclick_btn.configure(text=self.tr("button_working"), state="disabled")
            self.install_unirig_btn.configure(state="disabled")
            self.update_idletasks()
        except Exception:
            pass

        self._warn_if_comfyui_running()

        current_node_envs = detect_old_unirig_env(self.cfg.unirig_path)
        current_external_envs = detect_external_unirig_env_roots()
        needs_cleanup_confirmation = bool(current_node_envs or current_external_envs)

        if needs_cleanup_confirmation:
            authorized = self._ask_oneclick_authorization()
            self.log(f"One-click authorization popup result: {'yes' if authorized else 'no'}")
            if not authorized:
                self.current_action_key = "not_started"
                self.current_action.set(self.tr("not_started"))
                try:
                    self.oneclick_btn.configure(text=self.tr("oneclick"), state="normal")
                    self._apply_install_unirig_button_policy()
                except Exception:
                    pass
                return
        else:
            self.log("One-click authorization popup skipped: no previous UniRig environment detected")

        self.log("Pre-install cleanup policy: automatic forced cleanup of any existing UniRig env")
        self.install_running = True
        self.oneclick_btn.configure(state="disabled")
        self.install_unirig_btn.configure(state="disabled")
        self.set_progress_state("progress_running", True)
        threading.Thread(target=self._run_install, args=(True,), daemon=True).start()

    def _run_install(self, cleanup_confirmed=True):
        try:
            if not self.cfg.comfyui_path:
                self.log("Please run analysis first.")
                return
            self.current_action_key = "updating_env"
            self.current_action.set(self.tr("updating_env"))
            self.after(0, lambda: self.set_progress_state("progress_update", True))
            self.log("=== START INSTALL ===")
            self.log(f"Install branch: {self.cfg.env_mode or 'local'}")
            if (self.cfg.env_mode or '').lower() == 'embedded':
                self.log("Mode policy: embedded path preserved (validated branch)")
            elif (self.cfg.env_mode or '').lower() == 'venv':
                self.log("Mode policy: desktop/venv path enabled (no legacy __main__ fallback)")
            else:
                self.log("Mode policy: local/Desktop resources + user custom_nodes path enabled")
            self.log(self.tr("updating_env"))
            selected_target_version = get_target_comfy_env_version(self.cfg.env_mode)
            self.log(f"Comfy-env policy: unified={COMFY_ENV_VERSION}")
            update_comfy_env(self.cfg.python_path, self.cfg.env_mode, self.log)
            self.cfg.comfy_env_version = selected_target_version
            self.after(0, self._refresh_statuses_default)

            self.after(0, lambda: self.set_progress_state("progress_cleanup", True))
            if cleanup_confirmed:
                try:
                    removed_links, removed_external = force_cleanup_unirig_envs(self.cfg.unirig_path, self.log)
                except PermissionError as e:
                    messagebox.showwarning(self.tr("comfy_running_title"), self.tr("comfy_running_msg"), parent=self)
                    self.log(f"ComfyUI or a Python worker is still using the UniRig environment: {e}")
                    self.log("⚠ Installation interrompue : ComfyUI est encore ouvert")
                    self.current_action_key = "install_incomplete"
                    self.current_action.set(self.tr("install_incomplete"))
                    self.after(0, lambda: self.set_global_status("error", self.tr("install_incomplete"), "install_incomplete"))
                    self.after(0, lambda: self.set_progress_state("progress_error", False))
                    return
                except OSError as e:
                    if getattr(e, 'winerror', None) == 5:
                        messagebox.showwarning(self.tr("comfy_running_title"), self.tr("comfy_running_msg"), parent=self)
                        self.log(f"ComfyUI or a Python worker is still using the UniRig environment: {e}")
                        self.log("⚠ Installation interrompue : ComfyUI est encore ouvert")
                        self.current_action_key = "install_incomplete"
                        self.current_action.set(self.tr("install_incomplete"))
                        self.after(0, lambda: self.set_global_status("error", self.tr("install_incomplete"), "install_incomplete"))
                        self.after(0, lambda: self.set_progress_state("progress_error", False))
                        return
                    raise
                self.detected_old_envs = []
                self.log(f"Forced cleanup summary: node env links removed={removed_links}, external env roots removed={removed_external}")
                self.log("✔ " + self.tr("env_deleted"))
            else:
                self.log("⚠ " + self.tr("env_skip"))

            self.current_action_key = "installing_env"

            self.current_action.set(self.tr("installing_env"))
            self.after(0, lambda: self.set_progress_state("progress_install", True))
            self.log(self.tr("installing_env"))
            # V8.3 safety: re-check/install 3D preview support before environment build.
            self._ensure_3d_preview_support(install=True)
            install_result = install_unirig_env(self.cfg.python_path, self.cfg.unirig_path, self.cfg.env_mode, self.log)

            # Desktop venv / issue #53 policy:
            # do NOT rerun comfy-env install after a partial pixi result.
            # The official workaround is to stay on comfy-env 0.2.61 and continue with targeted wheel fallback,
            # because repeated comfy-env/pixi passes can panic again on local-version dist-info metadata.
            if (self.cfg.env_mode or '').lower() == 'venv' and install_result.get('status') == 'partial':
                self.log("=== SINGLE PASS POLICY (Desktop venv) ===")
                log_recovery_matrix_policy(self.log, "Recovery context after first comfy-env pass:")
                if install_result.get('reason') == 'pixi_metadata_panic':
                    self.log("Partial install detected: pixi metadata panic")
                    self.log("Policy: skip second comfy-env pass and continue to targeted wheel fallback")
                elif install_result.get('reason') == 'flash_attn_missing':
                    self.log("Partial install detected: flash-attn wheel missing")
                    self.log("Policy: skip second comfy-env pass and continue to targeted wheel fallback")
                elif install_result.get('reason') == 'flash_attn_timeout':
                    self.log("Partial install detected: flash-attn download timeout")
                    self.log("Policy: skip second comfy-env pass and continue to targeted wheel fallback with retries")

            self.current_action_key = "patching"

            self.current_action.set(self.tr("patching"))
            self.after(0, lambda: self.set_progress_state("progress_patch", True))

            extra_env_paths = [install_result.get("env_path", ""), install_result.get("build_dir", "")]
            if install_result.get("env_path"):
                self.log(f"Post-install discovery hint env_path: {install_result.get('env_path')}")
            if install_result.get("build_dir"):
                self.log(f"Post-install discovery hint build_dir: {install_result.get('build_dir')}")
            ensure_runtime_env_link(install_result.get("env_path", ""), install_result.get("build_dir", ""), self.log)
            apply_safe_unirig_patches(self.cfg.unirig_path, self.log)
            patches_ok, _patch_missing = validate_safe_unirig_patches(self.cfg.unirig_path, self.log)
            if not patches_ok:
                raise RuntimeError("UniRig patch validation failed")
            ok, missing, env_python = self.post_install_check(extra_env_paths)
            if env_python:
                extra_env_paths = [env_python] + extra_env_paths

            # If the second pass still leaves no env python, stop honestly here.
            if (not ok) and (not env_python):
                self.log("ERROR: No usable UniRig env python found after install and recovery passes")
                if (self.cfg.env_mode or '').lower() == 'venv':
                    self.log("Note: a real forced torch 2.7 build is not hard-coded here because the current source does not include a verified torch2.7 wheel matrix.")

            # Targeted fallback recovery for partial environments.
            if (not ok) and env_python and any(m in missing for m in ["torch_cluster", "torch_scatter", "flash_attn", "cumm", "spconv"]):
                self.log(f"⚠ modules missing after install: {', '.join(missing)}")
                if (self.cfg.env_mode or '').lower() == 'venv':
                    self.log("⚠ Desktop venv recovery: applying the explicit embedded-validated wheel matrix inside the isolated env.")
                    log_recovery_matrix_policy(self.log)
                self.fallback_install_missing(env_python, missing)
                ensure_runtime_env_link(install_result.get("env_path", ""), install_result.get("build_dir", ""), self.log)
                ok, missing, env_python = self.post_install_check([env_python] + extra_env_paths)

            patches_ok, _patch_missing = validate_safe_unirig_patches(self.cfg.unirig_path, self.log)
            if not patches_ok:
                ok = False
                if "patches" not in missing:
                    missing.append("patches")

            self.script_cache = build_install_script(self.cfg)
            script_path = Path(self.cfg.comfyui_path) / "SCRIPT_UNIRIG.ps1"
            script_path.write_text(self.script_cache, encoding="utf-8")
            self.log(f"{self.tr('script_generated')}: {script_path}")

            if ok:
                self.install_succeeded = True
                self.detected_old_envs = []
                self.after(0, lambda: self.status_old.set("✔ " + self.tr("env_ready"), GREEN_TXT))
                self.log(f"✅ {self.tr('install_done')}")
                self.log(self.tr("workflow_restart_hint"))
                self.log("Important : lancez ComfyUI en mode administrateur pour que les nodes UniRig apparaissent correctement.")
                self.log("⚠ PREVIEW NOTE: If Preview in ComfyUI appears empty or frozen, check the result in a 3D viewer.")
                self.current_action_key = "install_done"
                self.current_action.set(self.tr("install_done"))
                self.after(0, lambda: self.set_global_status("ok", self.tr("install_done"), "install_done"))
                self.after(0, lambda: self.set_progress_state("progress_done", False))
                self.after(0, lambda: messagebox.showinfo(APP_NAME, self.tr("install_finished_admin_msg"), parent=self))
            else:
                self.log(f"ERROR: Critical UniRig modules missing after install: {', '.join(missing)}")
                self.log(f"⚠ {self.tr('install_incomplete')}")
                self.current_action_key = "install_incomplete"
                self.current_action.set(self.tr("install_incomplete"))
                self.after(0, lambda: self.set_global_status("error", self.tr("install_incomplete"), "install_incomplete"))
                self.after(0, lambda: self.set_progress_state("progress_error", False))
        except Exception as e:
            self.log(f"ERROR: {e}")
            self.log(f"⚠ {self.tr('install_incomplete')}")
            self.current_action_key = "install_incomplete"
            self.current_action.set(self.tr("install_incomplete"))
            self.after(0, lambda: self.set_global_status("error", self.tr("install_incomplete"), "install_incomplete"))
            self.after(0, lambda: self.set_progress_state("progress_error", False))
        finally:
            self.after(0, lambda: self.oneclick_btn.configure(text=self.tr("oneclick"), state="normal"))
            self.after(0, self._apply_install_unirig_button_policy)
            self.install_running = False
            self._save_config()

    def log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {msg}")

    def flush_logs(self):
        pending = False
        while not self.log_queue.empty():
            if not pending:
                current = self.log_box.get("1.0", "end-1c").strip()
                if current == self.tr("log_placeholder"):
                    self.log_box.delete("1.0", "end")
                pending = True
            self.log_box.insert("end", self.log_queue.get() + "\n")
            self.log_box.see("end")
        self.after(100, self.flush_logs)

    def clear_log(self):
        self.log_box.delete("1.0", "end")
        self.log_box.insert("1.0", self.tr("log_placeholder"))

    def save_log(self):
        content = self.log_box.get("1.0", "end-1c")
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt"), ("All", "*.*")])
        if path:
            Path(path).write_text(content, encoding="utf-8")
            self.log("Journal sauvegardé" if self.lang.get().lower() == "fr" else "Log saved" if self.lang.get().lower() == "en" else "日志已保存")

    def export_script(self):
        if not self.script_cache:
            self.script_cache = build_install_script(self.cfg)
        path = filedialog.asksaveasfilename(defaultextension=".ps1", filetypes=[("Script", "*.ps1"), ("All", "*.*")])
        if path:
            Path(path).write_text(self.script_cache, encoding="utf-8")
            self.log(self.tr("script_saved"))

    def export_json(self):
        self._save_config()
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json"), ("All", "*.*")])
        if path:
            Path(path).write_text(json.dumps(asdict(self.cfg), indent=2, ensure_ascii=False), encoding="utf-8")
            self.log(self.tr("json_saved"))

    def _load_config(self):
        p = config_path()
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                self.cfg = InstallerConfig(**data)
                self.comfy_var.set(self.cfg.comfyui_path)
                self.unirig_var.set(self.cfg.unirig_path)
                self.python_var.set(self.cfg.python_path)
                if self.cfg.language in LANGS:
                    self.lang.set(self.cfg.language.upper())
            except Exception:
                pass

    def _save_config(self):
        self.cfg.comfyui_path = self.comfy_var.get().strip()
        self.cfg.unirig_path = self.unirig_var.get().strip()
        self.cfg.language = self.lang.get().lower()
        config_path().write_text(json.dumps(asdict(self.cfg), indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    App().mainloop()

def is_comfyui_running(comfyui_path: str) -> bool:
    """Best-effort Windows-friendly detection that ComfyUI is still running."""
    # Fast path: default local web UI port.
    for host in ("127.0.0.1", "localhost"):
        try:
            with socket.create_connection((host, 8188), timeout=0.35):
                return True
        except OSError:
            pass

    # Stronger fallback: inspect Python processes with executable path + command line.
    try:
        comfy_norm = str(Path(comfyui_path).resolve()).replace("'", "''").lower()
        ps = r"""
$procs = Get-CimInstance Win32_Process | Where-Object { $_.Name -match 'python|pythonw' };
foreach ($p in $procs) {
  $exe = ""
  try { $exe = (Get-Process -Id $p.ProcessId -ErrorAction Stop).Path } catch {}
  [PSCustomObject]@{
    ExecutablePath = $exe
    CommandLine    = $p.CommandLine
  } | ConvertTo-Json -Compress
}
"""
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
            check=False,
        )
        for line in (res.stdout or "").splitlines():
            line = (line or "").strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            exe = str(obj.get("ExecutablePath") or "").lower()
            cmd = str(obj.get("CommandLine") or "").lower()
            if comfy_norm and (
                comfy_norm in exe
                or comfy_norm in cmd
                or (exe.endswith("python.exe") and comfy_norm.replace("\\", "/") in cmd.replace("\\", "/"))
            ):
                return True
    except Exception:
        pass

    return False

