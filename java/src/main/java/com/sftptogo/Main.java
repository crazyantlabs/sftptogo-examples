package com.sftptogo;

import com.jcraft.jsch.JSchException;
import com.jcraft.jsch.SftpException;

public class Main {
    public static void main(String[] args) {
        var    host     = args[0];
        var    port     = Integer.parseInt(args[1]);
        var    username = args[2];
        var    password = args[3];
        var    base     = args[4];
        String keyPath  = null;
        if (args.length > 5) {
            keyPath = args[5];
        }
        var client = new SftpClient(host, port, username);
        try {
            if (keyPath != null && keyPath.length() > 1) {
                client.authKey(keyPath, password);
            } else {
                client.authPassword(password);
            }
            client.listFiles(base);
            client.uploadFile("./local.txt", base + "/remote.txt");
            client.downloadFile(base + "/remote.txt", "./download.txt");
            client.delete(base + "/remote.txt");
            client.close();
        } catch (JSchException | SftpException e) {
            e.printStackTrace();
        }
    }
}
