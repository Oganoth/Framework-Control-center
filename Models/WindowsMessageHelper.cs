using System;
using System.Runtime.InteropServices;

namespace FrameworkControl.Models
{
    public static class WindowsMessageHelper
    {
        private static IntPtr _oldWndProc;
        private static GlobalHotkey? _hotkeyManager;
        private static IntPtr _currentWindow;
        private static Win32Helper.WndProc? _wndProcDelegate;

        public static void RegisterMessageHandler(IntPtr hWnd, GlobalHotkey hotkeyManager)
        {
            if (hWnd == IntPtr.Zero)
                throw new ArgumentException("Window handle cannot be zero.", nameof(hWnd));
            if (hotkeyManager == null)
                throw new ArgumentNullException(nameof(hotkeyManager));

            _hotkeyManager = hotkeyManager;
            _currentWindow = hWnd;

            // Sauvegarder l'ancienne procédure de fenêtre
            _oldWndProc = Win32Helper.GetWindowLongPtr(hWnd, Win32Helper.GWL_WNDPROC);

            // Créer un nouveau gestionnaire de messages
            _wndProcDelegate = new Win32Helper.WndProc(WindowProc);
            if (!Win32Helper.SetWindowProc(hWnd, _wndProcDelegate))
            {
                throw new InvalidOperationException("Failed to set window procedure");
            }
        }

        private static IntPtr WindowProc(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam)
        {
            try
            {
                if (msg == Win32Helper.WM_HOTKEY && _hotkeyManager != null)
                {
                    _hotkeyManager.HandleHotkey((int)wParam);
                    return IntPtr.Zero;
                }
            }
            catch
            {
                // Ignorer les erreurs de gestion des raccourcis
            }

            // Appeler l'ancienne procédure de fenêtre pour tous les autres messages
            return Win32Helper.CallWindowProc(_oldWndProc, hWnd, msg, wParam, lParam);
        }

        public static void UnregisterMessageHandler()
        {
            if (_currentWindow != IntPtr.Zero && _oldWndProc != IntPtr.Zero)
            {
                try
                {
                    Win32Helper.SetWindowProc(_currentWindow, (hWnd, msg, wParam, lParam) =>
                        Win32Helper.CallWindowProc(_oldWndProc, hWnd, msg, wParam, lParam));
                }
                catch
                {
                    // Ignorer les erreurs lors de la restauration
                }
            }

            _oldWndProc = IntPtr.Zero;
            _currentWindow = IntPtr.Zero;
            _hotkeyManager = null;
            _wndProcDelegate = null;
        }
    }
} 