## Getting Started with SFTP using C#(.NET)

#Project Description

The project contains two solutions:
- SFTPClient: This is a simple console application which depicts how we can use our SFTP service to perform differnet file operations.
- SFPTService: This is a simple class library project that contains code to connect, upload ,download and delete files.

#Project Dependencies

- Install SSH.NET library from Nuget Pacakage.

# Getting Started 

1. First we need to instaill SSH.NET pacakage. We can either do this directly from the Pacakage manager or using the below command:

	dotnet add package SSH.NET --version 2020.0.0-beta1

2. Next, we need to define our SFTP Server configurations such as host name , port number , username and password.

	```cs
			public class SftpConfig
			{
				public string Host { get; set; }
				public int Port { get; set; }
				public string UserName { get; set; }
				public string Password { get; set; }
			}
	```

3. The next step is to simply call our SFTP service. Any operation performed inside the SFTP service would have to :

	- create an instance of SftpClient 
	- connect to the server, and perform the desired operation
	- close the connection


NOTE: The approach defined here only uses username and password for authnetication, however we can also use public keys for authentication

For this purpose we just have to replace the below line in SftpService.cs

FROM:

using var client = new SftpClient(_config.Host, _config.Port == 0 ? 22 : _config.Port, _config.UserName, _config.Password);

TO: 

var privateKey = new PrivateKeyFile(@"C:\some\path\key.pem");
using var client = new SftpClient(_config.Host, _config.UserName, new[] { privateKey });

where (@"C:\some\path\key.pem") defines the path to your public key