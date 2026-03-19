#!/usr/bin/env python3
"""
SFTP uploader with resume support.

Usage:
   python sftp_upload.py <local_path> <remote_path> [options]

Examples:
   python sftp_upload.py ./data.zip /uploads/data.zip
   python sftp_upload.py ./data.zip /uploads/data.zip --verify tail
   python sftp_upload.py ./data.zip /uploads/data.zip --host myserver.sftptogo.com --user myuser --key /path/to/key
"""

import paramiko
import os
import sys
import hashlib
import argparse
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type


class SFTPUploader:
   """SFTP client with resume support for interrupted uploads."""

   def __init__(self, hostname, port=22, username=None, key_path=None, password=None):
       """
       Initialize the SFTP uploader.

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
           # Auto-detect key type
           key_classes = [
               paramiko.Ed25519Key,
               paramiko.RSAKey,
               paramiko.ECDSAKey,
           ]
           private_key = None
           for key_class in key_classes:
               try:
                   private_key = key_class.from_private_key_file(self.key_path)
                   break
               except paramiko.SSHException:
                   continue
           if private_key is None:
               raise paramiko.SSHException(f"Unable to load key from {self.key_path}")
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

   def get_local_size(self, local_path):
       """Return size of local file."""
       return os.path.getsize(local_path)

   def get_local_mtime(self, local_path):
       """Return modification time of local file."""
       return os.path.getmtime(local_path)

   def get_remote_size(self, remote_path):
       """Return size of remote file, or 0 if it doesn't exist."""
       try:
           return self.sftp.stat(remote_path).st_size
       except FileNotFoundError:
           return 0

   def calculate_local_checksum(self, local_path, chunk_size=32768):
       """Calculate MD5 checksum of entire local file."""
       md5 = hashlib.md5()

       with open(local_path, "rb") as f:
           while True:
               chunk = f.read(chunk_size)
               if not chunk:
                   break
               md5.update(chunk)

       return md5.hexdigest()

   def calculate_local_tail_checksum(self, local_path, tail_size=1048576, chunk_size=32768):
       """
       Calculate MD5 checksum of the last portion of a local file.

       Much faster than full-file checksum while still detecting most changes.

       Args:
           local_path: Path to local file
           tail_size: Bytes to read from end of file (default: 1MB)
           chunk_size: Read chunk size in bytes

       Returns:
           Tuple of (checksum, file_size)
       """
       md5 = hashlib.md5()
       local_size = self.get_local_size(local_path)

       # For small files, just checksum the whole thing
       if local_size <= tail_size:
           return self.calculate_local_checksum(local_path, chunk_size), local_size

       start_pos = local_size - tail_size

       with open(local_path, "rb") as f:
           f.seek(start_pos)
           bytes_read = 0
           while bytes_read < tail_size:
               chunk = f.read(min(chunk_size, tail_size - bytes_read))
               if not chunk:
                   break
               md5.update(chunk)
               bytes_read += len(chunk)

       return md5.hexdigest(), local_size

   def _upload_with_resume(self, local_path, remote_path, chunk_size=32768):
       """
       Upload a file with resume support.

       Uses a .part file on the server during transfer and renames on success.
       Returns the total bytes uploaded in this session.
       """
       part_path = remote_path + ".part"

       local_size = self.get_local_size(local_path)

       # Check if remote .part file exists and get its size
       try:
           remote_size = self.sftp.stat(part_path).st_size
       except FileNotFoundError:
           remote_size = 0

       # Handle empty files
       if local_size == 0:
           print("Local file is empty (0 bytes)")
           with self.sftp.open(remote_path, 'w') as f:
               pass
           try:
               self.sftp.remove(part_path)
           except FileNotFoundError:
               pass
           return 0

       # Already complete?
       if remote_size >= local_size:
           print(f"File already complete ({remote_size:,} bytes)")
           try:
               self.sftp.remove(remote_path)
           except FileNotFoundError:
               pass
           self.sftp.rename(part_path, remote_path)
           return 0

       print(f"Local:  {local_size:,} bytes")
       print(f"Remote: {remote_size:,} bytes")
       if remote_size > 0:
           print(f"Resuming from byte {remote_size:,}")

       bytes_uploaded = 0

       # Open local file and seek to where we left off
       with open(local_path, 'rb') as local_file:
           local_file.seek(remote_size)

           # Open remote file in append mode
           with self.sftp.open(part_path, 'ab') as remote_file:
               while True:
                   chunk = local_file.read(chunk_size)
                   if not chunk:
                       break
                   remote_file.write(chunk)
                   bytes_uploaded += len(chunk)

                   total = remote_size + bytes_uploaded
                   percent = (total / local_size) * 100
                   print(f"\rProgress: {percent:.1f}% ({total:,}/{local_size:,} bytes)", end="", flush=True)

       print()

       # Verify and rename
       final_size = self.sftp.stat(part_path).st_size
       if final_size == local_size:
           try:
               self.sftp.remove(remote_path)
           except FileNotFoundError:
               pass
           self.sftp.rename(part_path, remote_path)
           print(f"Complete: {remote_path}")
       else:
           print(f"Size mismatch: expected {local_size:,}, got {final_size:,}")

       return bytes_uploaded

   def upload(self, local_path, remote_path, verify=None, tail_size=1048576, chunk_size=32768):
       """
       Upload with resume support and local file change detection.

       Always stores file size and modification timestamp in a local
       .upload.meta file to detect source file changes between attempts.
       Optionally runs a tail checksum for extra confidence.

       Args:
           local_path: Local source path
           remote_path: Path to file on server
           verify: Optional extra verification ("tail" for tail checksum)
           tail_size: Bytes to checksum from end of file when verify="tail" (default: 1MB)
           chunk_size: Upload chunk size in bytes
       """
       part_path = remote_path + ".part"
       meta_path = local_path + ".upload.meta"

       # Always store size + mtime to detect local file changes
       local_size = str(self.get_local_size(local_path))
       local_mtime = str(self.get_local_mtime(local_path))
       local_value = f"{local_size}:{local_mtime}"

       # Optionally add tail checksum for extra confidence
       if verify == "tail":
           print(f"Calculating local tail checksum (last {tail_size:,} bytes)...")
           checksum, _ = self.calculate_local_tail_checksum(local_path, tail_size, chunk_size)
           local_value = f"{local_value}:{checksum}"
           print(f"Local tail MD5: {checksum}")

       # Check if remote .part file exists
       try:
           remote_part_exists = self.sftp.stat(part_path)
       except FileNotFoundError:
           remote_part_exists = None

       # If remote .part exists but local .meta is missing, start fresh
       if remote_part_exists and not os.path.exists(meta_path):
           print("Partial upload found without metadata. Starting fresh.")
           self.sftp.remove(part_path)

       # Check for existing partial upload
       if remote_part_exists and os.path.exists(meta_path):
           with open(meta_path, "r") as f:
               saved_value = f.read().strip()

           if saved_value != str(local_value):
               print("Local file changed since last upload. Starting fresh.")
               self.sftp.remove(part_path)
               os.remove(meta_path)
           else:
               print("Source file unchanged. Resuming upload...")

       # Save current value for future verification
       with open(meta_path, "w") as f:
           f.write(str(local_value))

       # Upload
       self._upload_with_resume(local_path, remote_path, chunk_size)

       # Clean up meta file on success
       try:
           self.sftp.stat(remote_path)
           if os.path.exists(meta_path):
               os.remove(meta_path)
       except FileNotFoundError:
           pass

   @retry(
       stop=stop_after_attempt(3),
       wait=wait_fixed(5),
       retry=retry_if_exception_type((paramiko.SSHException, OSError, IOError)),
       reraise=True
   )
   def upload_with_retry(self, local_path, remote_path, verify=None, tail_size=1048576, chunk_size=32768):
       """
       Upload a file with automatic retry on connection failure.

       Args:
           local_path: Local source path
           remote_path: Path to file on server
           verify: Optional extra verification ("tail" for tail checksum)
           tail_size: Bytes to checksum from end of file when verify="tail"
           chunk_size: Upload chunk size in bytes

       Returns:
           True if upload completed successfully
       """
       try:
           self.connect()
           self.upload(local_path, remote_path, verify, tail_size, chunk_size)

           # Check if complete
           try:
               self.sftp.stat(remote_path)
               print("\nTransfer successful!")
               return True
           except FileNotFoundError:
               raise IOError("Upload incomplete")

       finally:
           self.disconnect()


def main():
   parser = argparse.ArgumentParser(
       description="Upload files over SFTP with resume support.",
       formatter_class=argparse.RawDescriptionHelpFormatter,
       epilog="""
Examples:
 %(prog)s ./data.zip /uploads/data.zip --host myserver.sftptogo.com --user myuser
 %(prog)s ./data.zip /uploads/data.zip --host myserver.com --key ~/.ssh/id_ed25519
 %(prog)s ./data.zip /uploads/data.zip --verify tail

The script always checks the local file's size and modification timestamp
before resuming. Use --verify tail to also checksum the last 1MB of the
file for extra confidence that the source hasn't changed.
       """
   )

   parser.add_argument("local_path", help="Local source file path")
   parser.add_argument("remote_path", help="Path on SFTP server")
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
       choices=["tail"],
       default=None,
       help="Extra verification: 'tail' checksums last 1MB of local file before resuming"
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
       help="Upload chunk size in bytes (default: 32768)"
   )

   args = parser.parse_args()

   # Validate required arguments
   if not args.host:
       parser.error("--host is required (or set SFTP_HOST environment variable)")
   if not args.user:
       parser.error("--user is required (or set SFTP_USER environment variable)")
   if not args.key and not args.password:
       parser.error("Either --key or --password is required")

   print(f"Uploading to {args.user}@{args.host}:{args.port}")
   print(f"Local file:  {args.local_path}")
   print(f"Remote file: {args.remote_path}")
   if args.verify:
       print(f"Extra verification: {args.verify}")

   uploader = SFTPUploader(
       hostname=args.host,
       port=args.port,
       username=args.user,
       key_path=args.key if args.key else None,
       password=args.password if args.password else None
   )

   try:
       success = uploader.upload_with_retry(
           local_path=args.local_path,
           remote_path=args.remote_path,
           verify=args.verify,
           tail_size=args.tail_size,
           chunk_size=args.chunk_size
       )
       sys.exit(0 if success else 1)
   except Exception as e:
       print(f"\nUpload failed after retries: {e}")
       sys.exit(1)


if __name__ == "__main__":
   main()

