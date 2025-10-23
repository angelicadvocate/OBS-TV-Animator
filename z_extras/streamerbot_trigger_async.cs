using System.Net.Http;
using System.Text;
using System.Threading.Tasks;

public class CPHInline
{
    public bool Execute()
    {
        // Fire and forget with proper async handling
        _ = SendTriggerAsync();
        return true; // Return immediately
    }

    private async Task SendTriggerAsync()
    {
        try
        {
            using (var client = new HttpClient())
            {
                client.Timeout = System.TimeSpan.FromSeconds(5);
                
                var url = "http://localhost:5000/trigger";
                var json = "{\"animation\":\"anim2.html\"}";
                var content = new StringContent(json, Encoding.UTF8, "application/json");

                var response = await client.PostAsync(url, content);
                
                if (response.IsSuccessStatusCode)
                {
                    var responseBody = await response.Content.ReadAsStringAsync();
                    CPH.LogInfo($"POST Success: {responseBody}");
                }
                else
                {
                    CPH.LogError($"POST Failed: {response.StatusCode} - {response.ReasonPhrase}");
                }
            }
        }
        catch (System.Exception ex)
        {
            CPH.LogError($"POST Error: {ex.Message}");
        }
    }
}