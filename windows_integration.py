
import ctypes
import os
import sys
import winreg

from PySide6.QtCore import QCoreApplication, QUrl
from PySide6.QtGui import QDesktopServices

from formats import ASSOCIATION_EXTENSIONS

APP_PROG_ID = "ELMASME.AssocFile"
APP_FRIENDLY_NAME = "ELMASME"
APP_DESCRIPTION = "Visor universal de archivos multimedia y documentos"

_ICON_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icons")


def _get_icon_path() -> str:
    icon_file = os.path.join(_ICON_DIR, "elmasme.ico")
    if os.path.isfile(icon_file):
        return icon_file
    exe = get_executable_path()
    if exe.lower().endswith(".exe"):
        return exe
    return ""


def get_executable_path() -> str:
    if getattr(sys, "frozen", False):
        return sys.executable
    return os.path.abspath(sys.argv[0])


def get_app_display_name() -> str:
    if getattr(sys, "frozen", False):
        name = os.path.splitext(os.path.basename(sys.executable))[0]
        return name
    return APP_FRIENDLY_NAME


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin():
    params = " ".join(f'"{arg}"' for arg in sys.argv[1:])
    executable = sys.executable if not getattr(sys, "frozen", False) else get_executable_path()

    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        executable,
        f'"{get_executable_path()}" {params}' if not getattr(sys, "frozen", False) else params,
        None,
        1,
    )


def _set_value(root, subkey: str, name: str, value: str):
    key = winreg.CreateKeyEx(root, subkey, 0, winreg.KEY_WRITE)
    winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
    winreg.CloseKey(key)


def _delete_tree(root, subkey: str):
    try:
        with winreg.OpenKey(root, subkey, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            while True:
                try:
                    child = winreg.EnumKey(key, 0)
                    _delete_tree(root, f"{subkey}\\{child}")
                except OSError:
                    break
    except OSError:
        pass

    try:
        winreg.DeleteKey(root, subkey)
    except OSError:
        pass


def _notify_shell():
    try:
        SHCNE_ASSOCCHANGED = 0x08000000
        SHCNF_IDLIST = 0x0000
        ctypes.windll.shell32.SHChangeNotify(
            SHCNE_ASSOCCHANGED, SHCNF_IDLIST, None, None
        )
    except Exception:
        pass


def register_file_associations():
    exe_path = get_executable_path()
    command = f'"{exe_path}" "%1"'
    icon_path = _get_icon_path()
    app_name = get_app_display_name()

    root = winreg.HKEY_CURRENT_USER
    cls = "Software\\Classes"

    _set_value(root, f"{cls}\\{APP_PROG_ID}", "", app_name)
    _set_value(root, f"{cls}\\{APP_PROG_ID}", "FriendlyTypeName", APP_DESCRIPTION)

    icon_target = f'"{icon_path}",0' if icon_path else f'"{exe_path}",0'
    _set_value(root, f"{cls}\\{APP_PROG_ID}\\DefaultIcon", "", icon_target)

    _set_value(root, f"{cls}\\{APP_PROG_ID}\\shell", "", "open")
    _set_value(root, f"{cls}\\{APP_PROG_ID}\\shell\\open", "", f"Abrir con {app_name}")
    _set_value(root, f"{cls}\\{APP_PROG_ID}\\shell\\open", "FriendlyAppName", app_name)
    _set_value(root, f"{cls}\\{APP_PROG_ID}\\shell\\open\\command", "", command)

    _set_value(
        root,
        f"Software\\RegisteredApplications",
        app_name,
        f"Software\\Classes\\{APP_PROG_ID}\\Capabilities",
    )

    _set_value(root, f"{cls}\\{APP_PROG_ID}\\Capabilities", "ApplicationName", app_name)
    _set_value(root, f"{cls}\\{APP_PROG_ID}\\Capabilities", "ApplicationDescription", APP_DESCRIPTION)

    for ext in ASSOCIATION_EXTENSIONS:
        _set_value(root, f"{cls}\\{ext}\\OpenWithProgids", APP_PROG_ID, "")

        _set_value(root, f"{cls}\\{APP_PROG_ID}\\Capabilities\\FileAssociations", ext, APP_PROG_ID)

    _notify_shell()
    QCoreApplication.processEvents()


def unregister_file_associations():
    root = winreg.HKEY_CURRENT_USER
    cls = "Software\\Classes"

    for ext in ASSOCIATION_EXTENSIONS:
        try:
            with winreg.OpenKey(root, f"{cls}\\{ext}\\OpenWithProgids", 0, winreg.KEY_WRITE) as key:
                winreg.DeleteValue(key, APP_PROG_ID)
        except OSError:
            pass

    app_name = get_app_display_name()
    try:
        with winreg.OpenKey(root, "Software\\RegisteredApplications", 0, winreg.KEY_WRITE) as key:
            winreg.DeleteValue(key, app_name)
    except OSError:
        pass

    _delete_tree(root, f"{cls}\\{APP_PROG_ID}")

    _notify_shell()
    QCoreApplication.processEvents()


def open_windows_default_apps_settings():
    QDesktopServices.openUrl(QUrl("ms-settings:defaultapps"))


def supported_extensions_text() -> str:
    from formats import (
        get_image_extensions, get_audio_extensions,
        get_video_extensions, get_document_extensions
    )

    lines = []
    lines.append("IMÁGENES:")
    lines.append(", ".join(get_image_extensions()))
    lines.append("")
    lines.append("AUDIO:")
    lines.append(", ".join(get_audio_extensions()))
    lines.append("")
    lines.append("VIDEO:")
    lines.append(", ".join(get_video_extensions()))
    lines.append("")
    lines.append("DOCUMENTOS:")
    lines.append(", ".join(get_document_extensions()))

    return "\n".join(lines)


def check_association_registered(ext: str) -> bool:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            f"Software\\Classes\\{ext}\\OpenWithProgids",
            0,
            winreg.KEY_READ
        ) as key:
            try:
                winreg.QueryValueEx(key, APP_PROG_ID)
                return True
            except OSError:
                return False
    except OSError:
        return False
