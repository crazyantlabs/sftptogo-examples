#!/usr/bin/env python3
"""
SFTP downloader with resume support.

Usage:
   python sftp_resume.py <remote_path> <local_path> [options]

Examples:
   python sftp_resume.py /uploads/data.zip ./data.zip
   python sftp_resume.py /uploads/data.zip ./data.zip --verify tail
   python sftp_resume.py /uploads/data.zip ./data.zip --verify checksum
   python sftp_resume.py /uploads/data.zip ./data.zip --host myserver.sftptogo.com --user myuser --key /path/to/key
"""

import paramiko
import os
import sys
import hashlib
import argparse
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type


class SFTPDownloader:
   """SFTP client with resume support for interrupted downloads."""

   def __init__(self, hostname, port=22, username=None, key_path=None, password=None):
       """
       Initialize the SFTP downloader.

       Args:
           hostname: SFTP server hostname
           port: SFTP server port (default: 22)
           username: SFTP username
           key_path: Path to SSH private key (optional)
           password: Password for auth (optional, used if no key_path)
       """
       self.hostname = hostname
       self.port = port
       self.username = username
       self.key_path = key_path
       self.password = password
       self.ssh = None
       self.sftp = None

   def connect(self):
       """Establish SSH and SFTP connections."""
       self.ssh = paramiko.SSHClient()
       self.ssh.load_system_host_keys()
       self.ssh.set_missing_host_key_policy(paramiko.RejectPolicy())

       if self.key_path:
           private_key = paramiko.Ed25519Key.from_private_key_file(self.key_path)
           self.ssh.connect(self.hostname, port=self.port, username=self.username, pkey=private_key)
       else:
           self.ssh.connect(self.hostname, port=self.port, username=self.username, password=self.password)

       self.sftp = self.ssh.open_sftp()

   def disconnect(self):
       """Close SFTP and SSH connections."""
       if self.sftp:
           self.sftp.close()
           self.sftp = None
       if self.ssh:
           self.ssh.close()
           self.ssh = None

   def __enter__(self):
       """Context manager entry."""
       self.connect()
       return self

   def __exit__(self, exc_type, exc_val, exc_tb):
       """Context manager exit."""
       self.disconnect()
       return False

   def get_remote_size(self, remote_path):
       """Return size of remote file."""
       return self.sftp.stat(remote_path).st_size

   def get_remote_mtime(self, remote_path):
       """Return modification time of remote file."""
       return self.sftp.stat(remote_path).st_mtime

   def calculate_remote_checksum(self, remote_path, chunk_size=32768):
       """Calculate MD5 checksum of entire remote file."""
       md5 = hashlib.md5()

       with self.sftp.open(remote_path, "rb") as f:
           while True:
               chunk = f.read(chunk_size)
               if not chunk:
                   break
               md5.update(chunk)

       return md5.hexdigest()

   def calculate_remote_tail_checksum(self, remote_path, tail_size=1048576, chunk_size=32768):
       """
       Calculate MD5 checksum of the last portion of a remote file.

       Much faster than full-file checksum while still detecting most changes.

       Args:
           remote_path: Path to file on server
           tail_size: Bytes to read from end of file (default: 1MB)
           chunk_size: Read chunk size in bytes

       Returns:
           Tuple of (checksum, file_size)
       """
       md5 = hashlib.md5()
       remote_size = self.get_remote_size(remote_path)

       # For small files, just checksum the whole thing
       if remote_size <= tail_size:
           return self.calculate_remote_checksum(remote_path, chunk_size), remote_size

       start_pos = remote_size - tail_size

       with self.sftp.open(remote_path, "rb") as f:
           f.seek(start_pos)
           bytes_read = 0
           while bytes_read < tail_size:
               chunk = f.read(min(chunk_size, tail_size - bytes_read))
               if not chunk:
                   break
               md5.update(chunk)
               bytes_read += len(chunk)

       return md5.hexdigest(), remote_size

   def _download_with_resume(self, remote_path, local_path, chunk_size=32768):
       """
       Download a file with resume support.

       Uses a .part file during transfer and renames on success.
       Returns the total bytes downloaded in this session.
       """
       part_path = local_path + ".part"

       remote_size = self.get_remote_size(remote_path)
       local_size = os.path.getsize(part_path) if os.path.exists(part_path) else 0

       if local_size >= remote_size:
           print(f"File already complete ({local_size:,} bytes)")
           if os.path.exists(part_path):
               os.rename(part_path, local_path)
           return 0

       print(f"Remote: {remote_size:,} bytes")
       print(f"Local:  {local_size:,} bytes")
       if local_size > 0:
           print(f"Resuming from byte {local_size:,}")

       bytes_downloaded = 0

       with self.sftp.open(remote_path, "rb") as remote_file:
           remote_file.seek(local_size)

           with open(part_path, "ab") as local_file:
               while True:
                   chunk = remote_file.read(chunk_size)
                   if not chunk:
                       break
                   local_file.write(chunk)
                   bytes_downloaded += len(chunk)

                   total = local_size + bytes_downloaded
                   percent = (total / remote_size) * 100
                   print(f"\rProgress: {percent:.1f}% ({total:,}/{remote_size:,} bytes)", end="", flush=True)

       print()

       final_size = os.path.getsize(part_path)
       if final_size == remote_size:
           os.rename(part_path, local_path)
           print(f"Complete: {local_path}")
       else:
           print(f"Size mismatch: expected {remote_size:,}, got {final_size:,}")

       return bytes_downloaded

   def download(self, remote_path, local_path, verify="size", tail_size=1048576, chunk_size=32768):
       """
       Download with the specified verification method.

       Args:
           remote_path: Path to file on server
           local_path: Local destination path
           verify: Verification method - "size", "timestamp", "checksum", or "tail"
           tail_size: Bytes to checksum from end of file when verify="tail" (default: 1MB)
           chunk_size: Download chunk size in bytes
       """
       part_path = local_path + ".part"
       meta_path = local_path + ".meta"

       if verify == "checksum":
           print("Calculating remote file checksum (full file)...")
           remote_value = self.calculate_remote_checksum(remote_path, chunk_size)
           print(f"Remote MD5: {remote_value}")
       elif verify == "tail":
           print(f"Calculating remote tail checksum (last {tail_size:,} bytes)...")
           checksum, size = self.calculate_remote_tail_checksum(remote_path, tail_size, chunk_size)
           remote_value = f"{checksum}:{size}"
           print(f"Remote tail MD5: {checksum} (file size: {size:,})")
       elif verify == "timestamp":
           remote_value = str(self.get_remote_mtime(remote_path))
       else:  # size
           remote_value = str(self.get_remote_size(remote_path))

       # Check for existing partial download
       if os.path.exists(part_path) and os.path.exists(meta_path):
           with open(meta_path, "r") as f:
               saved_value = f.read().strip()

           if saved_value != str(remote_value):
               print("Remote file changed since last download. Starting fresh.")
               os.remove(part_path)
               os.remove(meta_path)
           elif verify in ("checksum", "tail"):
               print("Checksum matches. Resuming download...")

       # Save current value for future verification
       with open(meta_path, "w") as f:
           f.write(str(remote_value))

       # Download
       self._download_with_resume(remote_path, local_path, chunk_size)

       # Clean up meta file on success
       if not os.path.exists(part_path) and os.path.exists(meta_path):
           os.remove(meta_path)

   @retry(
       stop=stop_after_attempt(3),
       wait=wait_fixed(5),
       retry=retry_if_exception_type((paramiko.SSHException, OSError, IOError)),
       reraise=True
   )
   def download_with_retry(self, remote_path, local_path, verify="size", tail_size=1048576, chunk_size=32768):
       """
       Download a file with automatic retry on connection failure.

       Args:
           remote_path: Path to file on server
           local_path: Local destination path
           verify: Verification method - "size", "timestamp", "checksum", or "tail"
           tail_size: Bytes to checksum from end of file when verify="tail"
           chunk_size: Download chunk size in bytes

       Returns:
           True if download completed successfully
       """
       try:
           self.connect()
           self.download(remote_path, local_path, verify, tail_size, chunk_size)

           # Check if complete
           part_path = local_path + ".part"
           if not os.path.exists(part_path):
               print("\nTransfer successful!")
               return True

           # Not complete, will retry
           raise IOError("Download incomplete")

       finally:
           self.disconnect()


def main():
   parser = argparse.ArgumentParser(
       description="Download files over SFTP with resume support.",
       formatter_class=argparse.RawDescriptionHelpFormatter,
       epilog="""
Examples:
 %(prog)s /uploads/data.zip ./data.zip --host myserver.sftptogo.com --user myuser
 %(prog)s /uploads/data.zip ./data.zip --host myserver.com --key ~/.ssh/id_ed25519
 %(prog)s /uploads/data.zip ./data.zip --verify tail
 %(prog)s /uploads/data.zip ./data.zip --verify checksum

Verification methods:
 size       Compare remote file size (default). Fast and works with all
            servers, including cloud-hosted services like SFTP To Go.
 timestamp  Compare modification time. Fast, but not recommended for
            S3-backed SFTP services where timestamps update on every upload.
 tail       Checksum last 1MB of file (or --tail-size bytes). Good balance
            of speed and reliability for large files.
 checksum   Calculate MD5 hash of entire remote file. Most reliable but
            slowest as it reads the whole file before resuming.
       """
   )

   parser.add_argument("remote_path", help="Path to file on SFTP server")
   parser.add_argument("local_path", help="Local destination path")
   parser.add_argument(
       "--host",
       default=os.environ.get("SFTP_HOST", ""),
       help="SFTP server hostname (or set SFTP_HOST env var)"
   )
   parser.add_argument(
       "--port",
       type=int,
       default=int(os.environ.get("SFTP_PORT", "22")),
       help="SFTP server port (default: 22)"
   )
   parser.add_argument(
       "--user",
       default=os.environ.get("SFTP_USER", ""),
       help="SFTP username (or set SFTP_USER env var)"
   )
   parser.add_argument(
       "--key",
       default=os.environ.get("SFTP_KEY", ""),
       help="Path to SSH private key (or set SFTP_KEY env var)"
   )
   parser.add_argument(
       "--password",
       default=os.environ.get("SFTP_PASSWORD", ""),
       help="SFTP password (or set SFTP_PASSWORD env var). Use --key instead when possible."
   )
   parser.add_argument(
       "--verify",
       choices=["size", "timestamp", "checksum", "tail"],
       default="size",
       help="Method to detect remote file changes (default: size)"
   )
   parser.add_argument(
       "--tail-size",
       type=int,
       default=1048576,
       help="Bytes to checksum when using --verify tail (default: 1048576 = 1MB)"
   )
   parser.add_argument(
       "--chunk-size",
       type=int,
       default=32768,
       help="Download chunk size in bytes (default: 32768)"
   )

   args = parser.parse_args()

   # Validate required arguments
   if not args.host:
       parser.error("--host is required (or set SFTP_HOST environment variable)")
   if not args.user:
       parser.error("--user is required (or set SFTP_USER environment variable)")
   if not args.key and not args.password:
       parser.error("Either --key or --password is required")

   print(f"Connecting to {args.user}@{args.host}:{args.port}")
   print(f"Remote file: {args.remote_path}")
   print(f"Local file:  {args.local_path}")
   print(f"Verification: {args.verify}")

   downloader = SFTPDownloader(
       hostname=args.host,
       port=args.port,
       username=args.user,
       key_path=args.key if args.key else None,
       password=args.password if args.password else None
   )

   try:
       success = downloader.download_with_retry(
           remote_path=args.remote_path,
           local_path=args.local_path,
           verify=args.verify,
           tail_size=args.tail_size,
           chunk_size=args.chunk_size
       )
       sys.exit(0 if success else 1)
   except Exception as e:
       print(f"\nDownload failed after retries: {e}")
       sys.exit(1)


if __name__ == "__main__":
   main()
