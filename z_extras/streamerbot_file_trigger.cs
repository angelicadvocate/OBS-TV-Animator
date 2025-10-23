using System;
using System.IO;

public class CPHInline
{
	public bool Execute()
	{
		CPH.LogInfo("🎬 StreamerBot File Trigger - Starting...");
		
		try
		{
			// Write a trigger file that the Python app watches
			var triggerFile = @"C:\Users\dalto\Documents\VS-Code\OBS-TV-Animator\OBS-TV-Animator\data\trigger.txt";
			
			// Change this animation name for different animations:
			// anim1.html, anim2.html, anim3.html, anim4.html, brb.html
			var animation = "anim2.html";
			
			CPH.LogInfo($"📂 Writing trigger file: {triggerFile}");
			CPH.LogInfo($"🎭 Animation: {animation}");
			
			// Ensure the directory exists
			var directory = Path.GetDirectoryName(triggerFile);
			if (!Directory.Exists(directory))
			{
				Directory.CreateDirectory(directory);
				CPH.LogInfo($"📁 Created directory: {directory}");
			}
			
			// Write the animation name to the file
			File.WriteAllText(triggerFile, animation);
			
			CPH.LogInfo("✅ Trigger file written successfully!");
			CPH.LogInfo($"🎯 Animation '{animation}' should now be displayed on TV");
			
			return true;
		}
		catch (Exception ex)
		{
			CPH.LogError($"❌ File write error: {ex.Message}");
			CPH.LogError($"🔍 Check if the path exists and StreamerBot has write permissions");
			return false;
		}
	}
}