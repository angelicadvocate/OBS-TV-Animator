using System;
using System.Net;
using System.Text;

public class CPHInline
{
	public bool Execute()
	{
		CPH.LogInfo("Starting animation trigger...");
		
		try
		{
			using (var client = new WebClient())
			{
				client.Headers[HttpRequestHeader.ContentType] = "application/json";
				
				var url = "http://localhost:5000/trigger";
				var json = "{\"animation\":\"anim2.html\"}";
				
				CPH.LogInfo($"Sending POST to: {url}");
				CPH.LogInfo($"JSON payload: {json}");
				
				var response = client.UploadString(url, json);
				
				CPH.LogInfo($"SUCCESS: {response}");
				return true;
			}
		}
		catch (Exception ex)
		{
			CPH.LogError($"ERROR: {ex.Message}");
			return false;
		}
	}
}