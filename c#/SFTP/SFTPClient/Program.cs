// See https://aka.ms/new-console-template for more information
using Microsoft.Extensions.Logging.Abstractions;
using SFTPService;



// Setup SFTP Configurations below and run the code directly 

    var config = new SftpConfig
    {
        Host = "", 
        Port = 0,
        UserName = "",
        Password = "" // 
    }; 

// Create the sftp service object 

    var sftpService = new SftpService(new NullLogger<SftpService>(), config);

// list files

    var files = sftpService.ListAllFiles("/directory/folder");
    foreach (var file in files)
    {
        if (file.IsDirectory)
        {
            Console.WriteLine($"Directory: [{file.FullName}]");
        }
        else if (file.IsRegularFile)
        {
            Console.WriteLine($"File: [{file.FullName}]");
        }
    }

// download a file

const string pngFile = @"test.png";
File.Delete(pngFile);
sftpService.DownloadFile(@"/folder/imap-console-client.png", pngFile);

if (File.Exists(pngFile))
{
    Console.WriteLine($"file {pngFile} downloaded");
}


// upload a file 
var testFile = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "test.txt");
sftpService.UploadFile(testFile, @"/folder/test.txt");

// delete a file
sftpService.DeleteFile(@"/folder/test.txt");