using Microsoft.Win32.TaskScheduler;
using System;
using System.IO;
using System.Runtime.Versioning;
using System.Security.Principal;
using FrameworkControl.Models;

namespace FrameworkControl.Helpers
{
    [SupportedOSPlatform("windows")]
    public static class StartupManager
    {
        private const string TaskName = "Framework Control Center";
        private const string TaskDescription = "Démarre Framework Control Center avec Windows";
        private static readonly Logger _logger = new Logger("StartupManager");

        public static void SetStartupState(bool enable)
        {
            try
            {
                _logger.Log($"========== Start SetStartupState({enable}) ==========");
                _logger.Log($"Current user: {WindowsIdentity.GetCurrent().Name}");
                _logger.Log($"Is elevated: {new WindowsPrincipal(WindowsIdentity.GetCurrent()).IsInRole(WindowsBuiltInRole.Administrator)}");

                using var ts = new TaskService();
                var existingTask = ts.GetTask(TaskName);

                if (existingTask != null)
                {
                    _logger.Log("Found existing task:");
                    _logger.Log($"- Name: {existingTask.Name}");
                    _logger.Log($"- Enabled: {existingTask.Enabled}");
                    _logger.Log($"- State: {existingTask.State}");
                    _logger.Log($"- Last Run Time: {existingTask.LastRunTime}");
                    _logger.Log($"- Last Run Result: {existingTask.LastTaskResult}");
                    if (existingTask.Definition?.Principal != null)
                    {
                        _logger.Log($"- Run Level: {existingTask.Definition.Principal.RunLevel}");
                        _logger.Log($"- Logon Type: {existingTask.Definition.Principal.LogonType}");
                        _logger.Log($"- User ID: {existingTask.Definition.Principal.UserId}");
                    }
                }

                if (enable)
                {
                    if (existingTask != null)
                    {
                        _logger.Log("Deleting existing task before creating new one");
                        ts.RootFolder.DeleteTask(TaskName);
                    }

                    _logger.Log("Creating new task");
                    var td = ts.NewTask();
                    td.RegistrationInfo.Description = TaskDescription;

                    // Configurer le déclencheur
                    var trigger = new LogonTrigger
                    {
                        Enabled = true,
                        Delay = TimeSpan.FromSeconds(10)
                    };
                    td.Triggers.Add(trigger);
                    _logger.Log("Added logon trigger with 10 seconds delay");

                    // Configurer l'action
                    var executablePath = System.Diagnostics.Process.GetCurrentProcess().MainModule?.FileName;
                    if (string.IsNullOrEmpty(executablePath))
                    {
                        _logger.LogError("Could not find executable path");
                        throw new InvalidOperationException("Impossible de trouver le chemin de l'exécutable.");
                    }

                    var workingDirectory = Path.GetDirectoryName(executablePath);
                    _logger.Log($"Executable path: {executablePath}");
                    _logger.Log($"Working directory: {workingDirectory}");
                    td.Actions.Add(new ExecAction(executablePath, null, workingDirectory));

                    // Configurer les paramètres de sécurité
                    td.Principal.RunLevel = TaskRunLevel.Highest;
                    td.Principal.LogonType = TaskLogonType.InteractiveToken;
                    td.Principal.UserId = WindowsIdentity.GetCurrent().Name;
                    _logger.Log("Configured security settings:");
                    _logger.Log($"- Run Level: {td.Principal.RunLevel}");
                    _logger.Log($"- Logon Type: {td.Principal.LogonType}");
                    _logger.Log($"- User ID: {td.Principal.UserId}");

                    // Configurer les paramètres généraux
                    td.Settings.DisallowStartIfOnBatteries = false;
                    td.Settings.StopIfGoingOnBatteries = false;
                    td.Settings.ExecutionTimeLimit = TimeSpan.Zero;
                    td.Settings.Hidden = false;
                    td.Settings.AllowHardTerminate = true;
                    td.Settings.StartWhenAvailable = true;
                    td.Settings.MultipleInstances = TaskInstancesPolicy.IgnoreNew;
                    td.Settings.RestartCount = 3;
                    td.Settings.RestartInterval = TimeSpan.FromMinutes(1);
                    td.Settings.RunOnlyIfNetworkAvailable = false;
                    _logger.Log("Configured general settings");

                    try
                    {
                        _logger.Log("Attempting to register task");
                        ts.RootFolder.RegisterTaskDefinition(
                            TaskName,
                            td,
                            TaskCreation.CreateOrUpdate,
                            WindowsIdentity.GetCurrent().Name,
                            null,
                            TaskLogonType.InteractiveToken);
                        _logger.Log("Task registered successfully");

                        // Vérifier que la tâche a été créée correctement
                        var createdTask = ts.GetTask(TaskName);
                        if (createdTask != null)
                        {
                            _logger.Log("Verified task creation:");
                            _logger.Log($"- Name: {createdTask.Name}");
                            _logger.Log($"- Enabled: {createdTask.Enabled}");
                            _logger.Log($"- State: {createdTask.State}");
                        }
                        else
                        {
                            _logger.LogError("Task was not found after creation!");
                        }
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError($"Failed to register task: {ex.Message}");
                        _logger.LogError($"Exception type: {ex.GetType().FullName}");
                        _logger.LogError($"Stack trace: {ex.StackTrace}");
                        throw;
                    }
                }
                else if (existingTask != null)
                {
                    _logger.Log("Deleting existing task");
                    ts.RootFolder.DeleteTask(TaskName);
                    _logger.Log("Task deleted successfully");

                    // Vérifier que la tâche a bien été supprimée
                    var deletedTask = ts.GetTask(TaskName);
                    if (deletedTask == null)
                    {
                        _logger.Log("Verified task deletion - task no longer exists");
                    }
                    else
                    {
                        _logger.LogError("Task still exists after deletion attempt!");
                    }
                }

                _logger.Log("========== End SetStartupState ==========");
            }
            catch (Exception ex)
            {
                _logger.LogError("========== Error in SetStartupState ==========");
                _logger.LogError($"Error message: {ex.Message}");
                _logger.LogError($"Exception type: {ex.GetType().FullName}");
                _logger.LogError($"Stack trace: {ex.StackTrace}");
                if (ex.InnerException != null)
                {
                    _logger.LogError("Inner exception:");
                    _logger.LogError($"- Message: {ex.InnerException.Message}");
                    _logger.LogError($"- Type: {ex.InnerException.GetType().FullName}");
                    _logger.LogError($"- Stack trace: {ex.InnerException.StackTrace}");
                }
                _logger.LogError("===========================================");
                throw;
            }
        }

        public static bool IsStartupEnabled()
        {
            try
            {
                _logger.Log("Checking startup state...");
                using var ts = new TaskService();
                var task = ts.GetTask(TaskName);
                var isEnabled = task != null && task.Enabled;
                _logger.Log($"Task exists: {task != null}");
                if (task != null)
                {
                    _logger.Log($"Task details:");
                    _logger.Log($"- Name: {task.Name}");
                    _logger.Log($"- Enabled: {task.Enabled}");
                    _logger.Log($"- State: {task.State}");
                    _logger.Log($"- Last Run Time: {task.LastRunTime}");
                    _logger.Log($"- Last Run Result: {task.LastTaskResult}");
                }
                _logger.Log($"IsStartupEnabled returning: {isEnabled}");
                return isEnabled;
            }
            catch (Exception ex)
            {
                _logger.LogError($"Error checking startup state: {ex.Message}");
                _logger.LogError($"Exception type: {ex.GetType().FullName}");
                _logger.LogError($"Stack trace: {ex.StackTrace}");
                return false;
            }
        }
    }
}
