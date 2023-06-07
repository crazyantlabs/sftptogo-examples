<?php

use phpseclib3\Net\SFTP;

class SFTPClient
{
  private $sftp;

  public function __construct($host, $port=22)
  {
    $this->sftp = new SFTP($host, $port);
    if (!$this->sftp->isConnected())
      throw new Exception("Failed to connect to ${host} on port ${port}.");
  }

  // Login with user and password
  public function auth_password($username, $password)
  {
    if (!$this->sftp->login($username, $password))
      throw new Exception("Failed to authenticate with username $username " .
                          "and password.");
  }

  // Login with SSH agent
  public function auth_agent($username)
  {
    if (!$this->sftp->login($username))
      throw new Exception("Failed to authenticate with username $username " .
                          "and public key.");
  }

  // Disconnect session
  public function disconnect()
  {
    $this->sftp->disconnect();
  }
  
  // List remote directory files
  function listFiles($remote_dir) {
    $tempArray = array();

    fwrite(STDOUT, "Listing [${remote_dir}] ...\n\n");

    $files = $this->sftp->nlist($remote_dir);
    foreach ($files as $file) {
      $filetype = $this->sftp->is_dir($file) ? 'dir' : 'file';
      $modTime = '';
      $size = sprintf("%.2f", $this->sftp->size($file));

      if ($filetype == "dir") {
        $file .= '/';
        $modTime = '';
        $size = "PRE";
      }

      $tempArray[] = $file;

      printf("%19s %12s %s\n", $modTime, $size, $file);
    }

    return $tempArray;
  }

  // Upload local file to remote file
  public function uploadFile($local_file, $remote_file)
  {
    fwrite(STDOUT, "Uploading [${local_file}] to [${remote_file}] ...\n");

    $data_to_send = file_get_contents($local_file);
    if ($data_to_send === false)
      throw new Exception("Could not open local file: $local_file.");

    if (!$this->sftp->put($remote_file, $data_to_send))
      throw new Exception("Could not send data from file: $local_file.");
  }

  // Download remote file to local file
  public function downloadFile($remote_file, $local_file)
  {
    fwrite(STDOUT, "Downloading [${remote_file}] to [${local_file}] ...\n");

    $contents = $this->sftp->get($remote_file);
    if ($contents === false)
      throw new Exception("Could not open remote file: $remote_file.");

    file_put_contents($local_file, $contents);
  }

  // Delete remote file
  public function deleteFile($remote_file){
    fwrite(STDOUT, "Deleting [${remote_file}] ...\n");
    $this->sftp->delete($remote_file);
  }
}

function main()
{
  $raw_url = getenv('SFTPTOGO_URL');

  // Parse URL
  $parsed_url = parse_url($raw_url);

  if ($parsed_url === false)
  {
    fwrite(STDERR, "Failed to parse SFTP To Go URL.\n");
    exit(1);
  }

  // Get user name and password
  $user = isset($parsed_url['user']) ? $parsed_url['user'] : null;
  $pass = isset($parsed_url['pass']) ? $parsed_url['pass'] : null;

  // Parse Host and Port
  $host = isset($parsed_url['host']) ? $parsed_url['host'] : null;

  // Port is always 22
  $port = isset($parsed_url['port']) ? $parsed_url['port'] : 22;

  fwrite(STDOUT, "Connecting to [${host}] ...\n");

  try
  {
    $client = new SFTPClient($host, $port);
    $client->auth_password($user, $pass);

    //*
    //* List working directory files
    //*
    $client->listFiles(".");

    //*
    //* Upload local file to remote file
    //*
    $client->uploadFile("./local.txt", "./remote.txt");

    //*
    //* Download remote file to local file
    //*
    $client->downloadFile("./remote.txt", "./download.txt");

    //*
    //* Delete remote file
    //*
    $client->deleteFile("./remote.txt");
  }
  catch (Exception $e)
  {
    echo $e->getMessage() . "\n";
  }
}

main();

?>
