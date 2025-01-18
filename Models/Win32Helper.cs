using System;
using System.Runtime.InteropServices;
using System.Threading;

namespace FrameworkControl.Models
{
    public static class Win32Helper
    {
        [DllImport("user32.dll")]
        public static extern IntPtr GetActiveWindow();

        [DllImport("user32.dll", SetLastError = true)]
        public static extern IntPtr SetWindowLongPtr(IntPtr hWnd, int nIndex, IntPtr dwNewLong);

        [DllImport("user32.dll", SetLastError = true)]
        public static extern IntPtr GetWindowLongPtr(IntPtr hWnd, int nIndex);

        [DllImport("user32.dll")]
        public static extern IntPtr CallWindowProc(IntPtr lpPrevWndFunc, IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);

        [DllImport("user32.dll")]
        public static extern IntPtr FindWindow(string? lpClassName, string lpWindowName);

        [DllImport("user32.dll")]
        public static extern bool EnumWindows(EnumWindowsProc enumProc, IntPtr lParam);

        [DllImport("user32.dll")]
        public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder lpString, int nMaxCount);

        [DllImport("user32.dll")]
        public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint lpdwProcessId);

        public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);
        public delegate IntPtr WndProc(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);

        public const int WM_HOTKEY = 0x0312;
        public const int GWL_WNDPROC = -4;

        private static IntPtr _foundHandle = IntPtr.Zero;
        private static string _searchTitle = string.Empty;
        private static uint _currentProcessId = (uint)System.Diagnostics.Process.GetCurrentProcess().Id;

        public static IntPtr GetWindowHandle(Avalonia.Controls.Window window)
        {
            if (window == null)
                throw new ArgumentNullException(nameof(window));
            if (string.IsNullOrEmpty(window.Title))
                throw new ArgumentException("Window must have a title", nameof(window));

            _foundHandle = IntPtr.Zero;
            _searchTitle = window.Title;

            // Attendre un peu que la fenêtre soit initialisée
            Thread.Sleep(100);

            // Énumérer toutes les fenêtres pour trouver celle qui correspond
            EnumWindows(EnumWindowCallback, IntPtr.Zero);

            // Si on n'a pas trouvé la fenêtre, utiliser GetActiveWindow comme fallback
            if (_foundHandle == IntPtr.Zero)
            {
                _foundHandle = GetActiveWindow();
            }

            return _foundHandle;
        }

        private static bool EnumWindowCallback(IntPtr hWnd, IntPtr lParam)
        {
            // Vérifier si la fenêtre appartient à notre processus
            uint processId;
            GetWindowThreadProcessId(hWnd, out processId);
            
            if (processId == _currentProcessId)
            {
                var builder = new System.Text.StringBuilder(256);
                if (GetWindowText(hWnd, builder, 256) > 0)
                {
                    if (builder.ToString() == _searchTitle)
                    {
                        _foundHandle = hWnd;
                        return false; // Arrêter l'énumération
                    }
                }
            }
            return true; // Continuer l'énumération
        }

        public static bool SetWindowProc(IntPtr hWnd, WndProc newWndProc)
        {
            try
            {
                var newWndProcPtr = Marshal.GetFunctionPointerForDelegate(newWndProc);
                var result = SetWindowLongPtr(hWnd, GWL_WNDPROC, newWndProcPtr);
                return result != IntPtr.Zero && Marshal.GetLastWin32Error() == 0;
            }
            catch
            {
                return false;
            }
        }
    }
} 