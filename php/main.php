<?php

class SFTPClient
{
  private $connection;
  private $sftp;

  public function __construct($host, $port=22)
  {
    $this->connection = @ssh2_connect($host, $port);
    if (! $this->connection)
      throw new Exception("Failed to connect to ${host} on port ${port}.");
  }

  // Login with user and password
  public function auth_password($username, $password)
  {
    if (! @ssh2_auth_password($this->connection, $username, $password))
      throw new Exception("Failed to authenticate with username $username " .
                          "and password.");

    $this->sftp = @ssh2_sftp($this->connection);
    if (! $this->sftp)
      throw new Exception("Could not initialize SFTP subsystem.");
  }

  // Login with SSH agent
  public function auth_agent($username)
  {
    if (! @ssh2_auth_agent($this->connection, $username))
      throw new Exception("Failed to authenticate with username $username " .
                          "and public key.");

    $this->sftp = @ssh2_sftp($this->connection);
    if (! $this->sftp)
      throw new Exception("Could not initialize SFTP subsystem.");
  }

  // List remote directory files
  function listFiles($remote_dir) {
    $sftp = $this->sftp;
    $realpath = ssh2_sftp_realpath($sftp, $remote_dir);
    $dir = "ssh2.sftp://$sftp$realpath";
    $tempArray = array();

    fwrite(STDOUT, "Listing [${remote_dir}] ...\n\n");

    if (is_dir($dir)) {
      if ($dh = opendir($dir)) {
        while (($file = readdir($dh)) !== false) {
          $realpath = ssh2_sftp_realpath($sftp, $file);
          $filetype = filetype($dir . $realpath);
          $modTime = "";
          $size = sprintf("%.2f", filesize($dir . $realpath));

          if($filetype == "dir") {
            $file = $file . "/";
            $modTime = "";
            $size = "PRE";
          }

          $tempArray[] = $file;

          printf("%19s %12s %s\n", $modTime, $size, $file);
        }
        closedir($dh);
      }
    }

    return $tempArray;
  }

  // Upload local file to remote file
  public function uploadFile($local_file, $remote_file)
  {
    fwrite(STDOUT, "Uploading [${local_file}] to [${remote_file}] ...\n");

    $sftp = $this->sftp;
    $realpath = ssh2_sftp_realpath($sftp, $remote_file);
    $stream = @fopen("ssh2.sftp://$sftp$realpath", 'w');
    if (! $stream)
      throw new Exception("Could not open file: $realpath");
    $data_to_send = @file_get_contents($local_file);
    if ($data_to_send === false)
      throw new Exception("Could not open local file: $local_file.");
    if (@fwrite($stream, $data_to_send) === false)
      throw new Exception("Could not send data from file: $local_file.");
    @fclose($stream);
  }

  // Download remote file to local file
  public function downloadFile($remote_file, $local_file)
  {
    fwrite(STDOUT, "Downloading [${remote_file}] to [${local_file}] ...\n");

    $sftp = $this->sftp;
    $realpath = ssh2_sftp_realpath($sftp, $remote_file);
    $stream = @fopen("ssh2.sftp://$sftp$realpath", 'r');
    if (! $stream)
      throw new Exception("Could not open file: $realpath");
    
    $local = fopen($local_file, "w");
    while(!feof($stream)){
      fwrite($local, fread($stream, 8192));
    }
    @fclose($stream);
    @fclose($local);
  }

  // Delete remote file
  public function deleteFile($remote_file){
    fwrite(STDOUT, "Deleting [${remote_file}] ...\n");
    $sftp = $this->sftp;
    $realpath = ssh2_sftp_realpath($sftp, $remote_file);
    unlink("ssh2.sftp://$sftp$realpath");
  }
}

function main()
{
  $raw_url = getenv('SFTPTOGO_URL');

  // Parse URL
  $parsed_url = parse_url($raw_url);

  if($parsed_url === false)
  {
    fwrite(STDERR, "Failed to parse SFTP To Go URL.\n");
    exit(1);
  }

  // Get user name and password
  $user = isset( $parsed_url['user'] ) ? $parsed_url['user'] : null;
  $pass = isset( $parsed_url['pass'] ) ? $parsed_url['pass'] : null;

  // Parse Host and Port
  $host = isset( $parsed_url['host'] ) ? $parsed_url['host'] : null;

  // Port is always 22
  $port = isset( $parsed_url['port'] ) ? $parsed_url['port'] : 22;

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
