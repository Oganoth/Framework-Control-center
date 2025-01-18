using Avalonia;
using Avalonia.Controls;
using Avalonia.Interactivity;
using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace FrameworkControl
{
    public partial class MessageDialog : Window, INotifyPropertyChanged
    {
        private string _dialogTitle = string.Empty;
        private string _message = string.Empty;

        public new event PropertyChangedEventHandler? PropertyChanged;

        public string DialogTitle
        {
            get => _dialogTitle;
            set
            {
                if (_dialogTitle != value)
                {
                    _dialogTitle = value;
                    OnPropertyChanged();
                }
            }
        }

        public string Message
        {
            get => _message;
            set
            {
                if (_message != value)
                {
                    _message = value;
                    OnPropertyChanged();
                }
            }
        }

        public MessageDialog()
        {
            InitializeComponent();
            DataContext = this;
        }

        private void OKButton_Click(object? sender, RoutedEventArgs e)
        {
            Close();
        }

        protected virtual void OnPropertyChanged([CallerMemberName] string? propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }
} 