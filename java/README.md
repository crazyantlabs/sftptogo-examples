Getting started with JAVA and SFTP to Go
======================================

The code in this directory contains sample code in JAVA, that accompanies the tutorial that can be found [here](__).
This example is built using gradle. We used the [JSCH](http://www.jcraft.com/jsch/) for this example.

## Running The Example

1. Download the dependencies and build project

```shell
./gradlew build
```

2. Running the example

```shell
./gradlew run --args="<host> <port> <username> <password> <base directory on server>"
```

## Adding JSCH to Project

There are number of ways to add JSCH in your java project

### Using Maven

```
<dependency>
    <groupId>com.jcraft</groupId>
    <artifactId>jsch</artifactId>
    <version>0.1.55</version>
</dependency>
```

### Using Gradle

```
implementation 'com.jcraft:jsch:0.1.55'
```

If you are using other build tools for your project please refer to [JSCH](http://www.jcraft.com/jsch/)
documentation to add it in your project.