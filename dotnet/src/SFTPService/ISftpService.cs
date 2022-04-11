using Renci.SshNet.Sftp;

namespace SFTPService
{
    /// <summary>
    /// This interface contains methods that are supported by our sftp service 
    /// </summary>
    public interface ISftpService
    {
        /// <summary>
        /// Get list of all the files in remote directory
        /// </summary>
        /// <param name="remoteDirectory">is the directory path.</param>
        /// <returns>IEnumerable<SftpFile> , containing collection of files in the given directory</returns>
        IEnumerable<SftpFile> ListAllFiles(string remoteDirectory = ".");

        /// <summary>
        /// Upload the files from a local directory to the remote directory
        /// </summary>
        /// <param name="localFilePath">is the source path of the file .</param>
        /// <param name="remoteFilePath">is the destination path of the file .</param>
        /// <returns>void</returns>
        void UploadFile(string localFilePath, string remoteFilePath);

        /// <summary>
        /// download the files from remote location to local path
        /// </summary>
        /// <param name="localFilePath">is the source path of the file .</param>
        /// <param name="remoteFilePath">is the destination path of the file .</param>
        /// <returns>void</returns>
        void DownloadFile(string remoteFilePath, string localFilePath);


        /// <summary>
        /// delete the remote files 
        /// </summary>     
        /// <param name="remoteFilePath">is the path of the file to be deleted .</param>
        /// <returns>void</returns>
        void DeleteFile(string remoteFilePath);
    }
}
