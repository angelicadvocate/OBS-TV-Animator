using System;
using System.Diagnostics;

public class CPHInline
{
	public bool Execute()
	{
		CPH.LogInfo("Starting animation trigger via PowerShell...");
		
		try
		{
			var startInfo = new ProcessStartInfo()
			{
				FileName = "powershell.exe",
				Arguments = "-Command \"Invoke-RestMethod -Uri 'http://localhost:5000/trigger' -Method POST -ContentType 'application/json' -Body '{\\\"animation\\\":\\\"anim2.html\\\"}'\"",
				UseShellExecute = false,
				RedirectStandardOutput = true,
				RedirectStandardError = true,
				CreateNoWindow = true
			};

			CPH.LogInfo("Executing PowerShell command...");

			using (var process = Process.Start(startInfo))
			{
				var output = process.StandardOutput.ReadToEnd();
				var error = process.StandardError.ReadToEnd();
				
				process.WaitForExit();

				if (process.ExitCode == 0)
				{
					CPH.LogInfo($"SUCCESS: {output}");
					return true;
				}
				else
				{
					CPH.LogError($"PowerShell failed with exit code {process.ExitCode}");
					CPH.LogError($"Error: {error}");
					return false;
				}
			}
		}
		catch (Exception ex)
		{
			CPH.LogError($"ERROR: {ex.Message}");
			return false;
		}
	}
}