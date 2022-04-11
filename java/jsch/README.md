Getting started with JAVA and SFTP to Go
======================================

The code in this directory contains sample code in JAVA, that accompanies the tutorial that can be found [here](__).
This example is built using gradle. We used the [JSCH](https://github.com/mwiede/jsch) for this example.

## Running The Example

1. Download the dependencies and build project

```shell
./gradlew build
```

2. Running the example

```shell
./gradlew run --args="<host> <port> <username> <password>  <base directory on server> <private key path can be empty>"
```

## Adding JSCH to Project

There are number of ways to add JSCH in your java project

### Using Maven

```
<dependency>
    <groupId>com.github.mwiede</groupId>
    <artifactId>jsch</artifactId>
    <version>0.2.0</version>
</dependency>
```

### Using Gradle

```
implementation 'com.github.mwiede:jsch:0.2.0'
```

If you are using other build tools for your project please refer to [JSCH](https://github.com/mwiede/jsch)
documentation to add it in your project.