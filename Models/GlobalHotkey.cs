using System;
using System.Runtime.InteropServices;
using System.Collections.Generic;
using Avalonia.Input;

namespace FrameworkControl.Models
{
    public class GlobalHotkey : IDisposable
    {
        [DllImport("user32.dll")]
        private static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);

        [DllImport("user32.dll")]
        private static extern bool UnregisterHotKey(IntPtr hWnd, int id);

        private readonly IntPtr _windowHandle;
        private readonly Dictionary<int, Action> _hotkeyActions = new();
        private readonly object _lockObject = new();
        private int _currentId = 0;
        private bool _isDisposed;

        public GlobalHotkey(IntPtr windowHandle)
        {
            if (windowHandle == IntPtr.Zero)
                throw new ArgumentException("Window handle cannot be zero.", nameof(windowHandle));

            _windowHandle = windowHandle;
        }

        public int RegisterHotkey(Key key, Action callback)
        {
            if (callback == null)
                throw new ArgumentNullException(nameof(callback));

            if (_isDisposed)
                throw new ObjectDisposedException(nameof(GlobalHotkey));

            lock (_lockObject)
            {
                try
                {
                    uint vk = (uint)KeyToVirtualKey(key);
                    var id = ++_currentId;

                    if (RegisterHotKey(_windowHandle, id, 0, vk))
                    {
                        _hotkeyActions[id] = callback;
                        return id;
                    }

                    throw new InvalidOperationException($"Failed to register hotkey {key}. The key might be already registered by another application.");
                }
                catch (Exception ex)
                {
                    throw new InvalidOperationException($"Error registering hotkey: {ex.Message}", ex);
                }
            }
        }

        private int KeyToVirtualKey(Key key)
        {
            // Codes virtuels Windows (VK) pour les touches courantes
            switch (key)
            {
                // Touches de fonction
                case Key.F1: return 0x70;
                case Key.F2: return 0x71;
                case Key.F3: return 0x72;
                case Key.F4: return 0x73;
                case Key.F5: return 0x74;
                case Key.F6: return 0x75;
                case Key.F7: return 0x76;
                case Key.F8: return 0x77;
                case Key.F9: return 0x78;
                case Key.F10: return 0x79;
                case Key.F11: return 0x7A;
                case Key.F12: return 0x7B;

                // Touches alphanumériques
                case Key.A: return 0x41;
                case Key.B: return 0x42;
                case Key.C: return 0x43;
                case Key.D: return 0x44;
                case Key.E: return 0x45;
                case Key.F: return 0x46;
                case Key.G: return 0x47;
                case Key.H: return 0x48;
                case Key.I: return 0x49;
                case Key.J: return 0x4A;
                case Key.K: return 0x4B;
                case Key.L: return 0x4C;
                case Key.M: return 0x4D;
                case Key.N: return 0x4E;
                case Key.O: return 0x4F;
                case Key.P: return 0x50;
                case Key.Q: return 0x51;
                case Key.R: return 0x52;
                case Key.S: return 0x53;
                case Key.T: return 0x54;
                case Key.U: return 0x55;
                case Key.V: return 0x56;
                case Key.W: return 0x57;
                case Key.X: return 0x58;
                case Key.Y: return 0x59;
                case Key.Z: return 0x5A;

                // Touches numériques
                case Key.D0: return 0x30;
                case Key.D1: return 0x31;
                case Key.D2: return 0x32;
                case Key.D3: return 0x33;
                case Key.D4: return 0x34;
                case Key.D5: return 0x35;
                case Key.D6: return 0x36;
                case Key.D7: return 0x37;
                case Key.D8: return 0x38;
                case Key.D9: return 0x39;

                // Touches spéciales
                case Key.Tab: return 0x09;
                case Key.Enter: return 0x0D;
                case Key.Space: return 0x20;
                case Key.Delete: return 0x2E;
                case Key.Back: return 0x08;
                case Key.Home: return 0x24;
                case Key.End: return 0x23;
                case Key.PageUp: return 0x21;
                case Key.PageDown: return 0x22;
                case Key.Insert: return 0x2D;

                // Touches de direction
                case Key.Left: return 0x25;
                case Key.Up: return 0x26;
                case Key.Right: return 0x27;
                case Key.Down: return 0x28;

                default:
                    throw new ArgumentException($"Unsupported key: {key}");
            }
        }

        public void UnregisterHotkey(int id)
        {
            if (_isDisposed)
                return;

            lock (_lockObject)
            {
                if (_hotkeyActions.ContainsKey(id))
                {
                    try
                    {
                        if (UnregisterHotKey(_windowHandle, id))
                        {
                            _hotkeyActions.Remove(id);
                        }
                    }
                    catch
                    {
                        // Ignorer les erreurs lors de la désinscription
                    }
                }
            }
        }

        public void HandleHotkey(int id)
        {
            if (_isDisposed)
                return;

            Action? action = null;
            lock (_lockObject)
            {
                if (_hotkeyActions.TryGetValue(id, out var callback))
                {
                    action = callback;
                }
            }

            action?.Invoke();
        }

        public void Dispose()
        {
            if (_isDisposed)
                return;

            lock (_lockObject)
            {
                foreach (var id in _hotkeyActions.Keys)
                {
                    UnregisterHotKey(_windowHandle, id);
                }
                _hotkeyActions.Clear();
                _isDisposed = true;
            }
        }

        protected virtual void Dispose(bool disposing)
        {
            if (!_isDisposed)
            {
                if (disposing)
                {
                    lock (_lockObject)
                    {
                        foreach (var id in _hotkeyActions.Keys)
                        {
                            try
                            {
                                UnregisterHotKey(_windowHandle, id);
                            }
                            catch
                            {
                                // Ignorer les erreurs lors de la désinscription
                            }
                        }
                        _hotkeyActions.Clear();
                    }
                }
                _isDisposed = true;
            }
        }

        ~GlobalHotkey()
        {
            Dispose(false);
        }
    }
}