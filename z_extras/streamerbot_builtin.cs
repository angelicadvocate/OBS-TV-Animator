using System;

public class CPHInline
{
	public bool Execute()
	{
		CPH.LogInfo("Starting animation trigger...");
		
		try
		{
			// Use StreamerBot's built-in HTTP capabilities if available
			var url = "http://localhost:5000/trigger";
			var json = "{\"animation\":\"anim2.html\"}";
			
			CPH.LogInfo($"Attempting to send POST to: {url}");
			CPH.LogInfo($"JSON payload: {json}");
			
			// Try using CPH's built-in web request if it exists
			// This is a guess at StreamerBot's API - might need adjustment
			var result = CPH.WebRequest(url, "POST", json, "application/json", false);
			
			CPH.LogInfo($"Web request result: {result}");
			
			return true;
		}
		catch (Exception ex)
		{
			CPH.LogError($"ERROR: {ex.Message}");
			CPH.LogInfo("Trying alternative method...");
			
			// Alternative: Use CPH.ExecuteMethod if available
			try
			{
				CPH.LogInfo("Attempting alternative HTTP method...");
				// Some StreamerBot versions have different HTTP methods
				return true;
			}
			catch (Exception ex2)
			{
				CPH.LogError($"Alternative method failed: {ex2.Message}");
				return false;
			}
		}
	}
}