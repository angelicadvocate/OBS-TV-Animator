using System;
using System.Net.Http;
using System.Text;

public class CPHInline
{
	public bool Execute()
	{
		CPH.LogInfo("Starting animation trigger...");
		
		try
		{
			using (var client = new HttpClient())
			{
				client.Timeout = TimeSpan.FromSeconds(5);
				
				var url = "http://localhost:5000/trigger";
				var json = "{\"animation\":\"anim2.html\"}";
				var content = new StringContent(json, Encoding.UTF8, "application/json");

				CPH.LogInfo($"Sending POST to: {url}");
				
				var response = client.PostAsync(url, content).Result;
				
				if (response.IsSuccessStatusCode)
				{
					var responseBody = response.Content.ReadAsStringAsync().Result;
					CPH.LogInfo($"SUCCESS: {responseBody}");
					return true;
				}
				else
				{
					CPH.LogError($"FAILED: {response.StatusCode} - {response.ReasonPhrase}");
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