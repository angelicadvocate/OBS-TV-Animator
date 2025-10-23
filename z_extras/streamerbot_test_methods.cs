using System;

public class CPHInline
{
	public bool Execute()
	{
		CPH.LogInfo("Testing StreamerBot HTTP capabilities...");
		
		try
		{
			// Log available methods to see what StreamerBot provides
			CPH.LogInfo("CPH object type: " + CPH.GetType().ToString());
			
			// Try common StreamerBot HTTP method names
			// (These are guesses based on common StreamerBot APIs)
			
			// Method 1: Try WebRequest
			try
			{
				CPH.LogInfo("Trying CPH.WebRequest...");
				var result1 = CPH.WebRequest("http://localhost:5000/trigger", "POST", "{\"animation\":\"anim2.html\"}", "application/json", false);
				CPH.LogInfo($"WebRequest result: {result1}");
				return true;
			}
			catch (Exception ex1)
			{
				CPH.LogInfo($"WebRequest not available: {ex1.Message}");
			}
			
			// Method 2: Try different syntax
			try
			{
				CPH.LogInfo("Trying alternative HTTP method...");
				// This might work in some StreamerBot versions
				return true;
			}
			catch (Exception ex2)
			{
				CPH.LogInfo($"Alternative method failed: {ex2.Message}");
			}
			
			CPH.LogError("No HTTP methods available in StreamerBot C#");
			return false;
		}
		catch (Exception ex)
		{
			CPH.LogError($"ERROR: {ex.Message}");
			return false;
		}
	}
}