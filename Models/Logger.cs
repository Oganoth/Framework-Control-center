using System;
using System.IO;
using System.Text;
using Avalonia;
using Avalonia.Logging;

namespace FrameworkControl.Models
{
    public class Logger : ILogger
    {
        private static readonly string LogDirectory = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "logs");
        private static readonly string LogFile = Path.Combine(LogDirectory, "app_log.txt");
        private static readonly object LockObj = new object();
        private readonly string _source;
        private readonly LogEventLevel _minimumLevel;

        static Logger()
        {
            // Ensure logs directory exists
            if (!Directory.Exists(LogDirectory))
            {
                Directory.CreateDirectory(LogDirectory);
            }
        }

        public Logger(string source, LogEventLevel minimumLevel = LogEventLevel.Information)
        {
            _source = source;
            _minimumLevel = minimumLevel;
        }

        public void Log(string message, LogEventLevel level = LogEventLevel.Information)
        {
            if (level < _minimumLevel) return;

            var logMessage = $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] [{_source}] {message}";
            
            // Log to Avalonia
            global::Avalonia.Logging.Logger.TryGet(LogEventLevel.Information, _source)?.Log(this, logMessage);

            try
            {
                lock (LockObj)
                {
                    File.AppendAllText(LogFile, logMessage + Environment.NewLine);
                }
            }
            catch (Exception ex)
            {
                global::Avalonia.Logging.Logger.TryGet(LogEventLevel.Error, _source)?.Log(this, $"Error writing to log file: {ex.Message}");
            }
        }

        public void LogCommand(string command, string arguments, string? output = null, string? error = null, int? exitCode = null)
        {
            var sb = new StringBuilder();
            sb.AppendLine($"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] [{_source}] Executing command:");
            sb.AppendLine($"Command: {command} {arguments}");
            
            if (output != null)
            {
                sb.AppendLine("Output:");
                sb.AppendLine(output);
            }
            
            if (error != null)
            {
                sb.AppendLine("Error:");
                sb.AppendLine(error);
                // Log errors with Error level
                global::Avalonia.Logging.Logger.TryGet(LogEventLevel.Error, _source)?.Log(this, error);
            }
            
            if (exitCode.HasValue)
            {
                var exitMessage = $"Exit code: {exitCode}";
                sb.AppendLine(exitMessage);
                
                // Log non-zero exit codes with Warning level
                if (exitCode != 0)
                {
                    global::Avalonia.Logging.Logger.TryGet(LogEventLevel.Warning, _source)?.Log(this, exitMessage);
                }
            }
            
            sb.AppendLine(new string('-', 80));

            try
            {
                lock (LockObj)
                {
                    File.AppendAllText(LogFile, sb.ToString());
                }
            }
            catch (Exception ex)
            {
                global::Avalonia.Logging.Logger.TryGet(LogEventLevel.Error, _source)?.Log(this, $"Error writing to log file: {ex.Message}");
            }
        }

        public void LogError(string message)
        {
            Log(message, LogEventLevel.Error);
        }

        public void LogWarning(string message)
        {
            Log(message, LogEventLevel.Warning);
        }

        public void LogDebug(string message)
        {
            Log(message, LogEventLevel.Debug);
        }

        public void Error(string message)
        {
            Log($"ERROR: {message}", LogEventLevel.Error);
        }
    }
}
