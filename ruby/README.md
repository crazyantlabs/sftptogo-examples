Getting started with Ruby and SFTP To Go
========================================

The code in this directory contains sample code in Ruby for using SFTP To Go.

## Install

Ruby doesn't come bundled with the SFTP libraries from the get-go, so we’ll need to install the required [net-sftp](https://rubygems.org/gems/net-sftp/versions/2.1.2) gem using bundler.

```
$ bundle install
```

In accordance with the 12 factor app cloud development methodology, you should explicitly define your app's dependencies, which would make our Gemfile file look like this:

```
source 'https://rubygems.org'

gem 'net-sftp', '~> 2.1', '>= 2.1.2'
```

## Run

We'll use the environment variable SFTPTOGO_URL to obtain all the required information for connecting to an SFTP server in a URI format: `sftp://user:password@host`.

Within our SFTPClient class initializer, the variable is parsed to extract the username, password, host and optional port.

Running the example will do the following:

1. **List** home directory files (to standard output).
2. **Write**) a sample file to the remote home directory.
3. **Download** the sample file to `download.txt` file so you can see the remote file, locally.
4. **Upload** the downloaded file to another remote copy.
5. Write a sample **CSV data** to the remote home directory.
6. Process the remote CSV file in-memory and print its content (without the headers).

```
$ ruby main.rb
```
