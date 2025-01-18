using Avalonia.Logging;

namespace FrameworkControl.Models
{
    public interface ILogger
    {
        void Log(string message, LogEventLevel level = LogEventLevel.Information);
        void LogCommand(string command, string arguments, string? output = null, string? error = null, int? exitCode = null);
        void LogError(string message);
        void LogWarning(string message);
        void LogDebug(string message);
    }
}
