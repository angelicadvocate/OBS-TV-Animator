using System.Net.Http;
using System.Text;

public class CPHInline
{
    public bool Execute()
    {
        CPH.LogInfo("Starting trigger execution...");
        
        try
        {
            CPH.LogInfo("Creating HTTP client...");
            
            // Use a synchronous approach that's more reliable in StreamerBot
            using (var client = new HttpClient())
            {
                client.Timeout = System.TimeSpan.FromSeconds(5); // 5 second timeout
                
                var url = "http://localhost:5000/trigger";
                var json = "{\"animation\":\"anim2.html\"}";
                var content = new StringContent(json, Encoding.UTF8, "application/json");

                CPH.LogInfo($"Sending POST to: {url}");
                CPH.LogInfo($"JSON payload: {json}");

                // Make the POST request synchronously
                var response = client.PostAsync(url, content).Result;
                
                if (response.IsSuccessStatusCode)
                {
                    var responseBody = response.Content.ReadAsStringAsync().Result;
                    CPH.LogInfo($"POST Success: {responseBody}");
                    return true;
                }
                else
                {
                    CPH.LogError($"POST Failed: {response.StatusCode} - {response.ReasonPhrase}");
                    return false;
                }
            }
        }
        catch (System.Exception ex)
        {
            CPH.LogError($"POST Error: {ex.Message}");
            return false;
        }
    }
}