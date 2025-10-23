using System;
using System.IO;
using System.Net;
using System.Text;

public class CPHInline
{
	public bool Execute()
	{
		CPH.LogInfo("Starting animation trigger...");
		
		try
		{
			var url = "http://localhost:5000/trigger";
			var json = "{\"animation\":\"anim2.html\"}";
			
			CPH.LogInfo($"Sending POST to: {url}");
			
			var request = WebRequest.Create(url);
			request.Method = "POST";
			request.ContentType = "application/json";
			
			var data = Encoding.UTF8.GetBytes(json);
			request.ContentLength = data.Length;
			
			using (var stream = request.GetRequestStream())
			{
				stream.Write(data, 0, data.Length);
			}
			
			using (var response = request.GetResponse())
			using (var responseStream = response.GetResponseStream())
			using (var reader = new StreamReader(responseStream))
			{
				var responseText = reader.ReadToEnd();
				CPH.LogInfo($"SUCCESS: {responseText}");
			}
			
			return true;
		}
		catch (Exception ex)
		{
			CPH.LogError($"ERROR: {ex.Message}");
			return false;
		}
	}
}