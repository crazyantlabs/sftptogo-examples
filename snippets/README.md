<a href="https://sftptogo.com/"><img alt="SFTP To Go logo" src="https://sftptogo.com/images/logo.svg" height="80" /></a>

_SFTP To Go: Managed cloud storage as a Service_

*Secure cloud storage with SFTP / FTPS / S3 / HTTP file access designed for smooth and easy data transfer and storage.*

SFTP To Go code snippets
========================

The SFTP To Go code snippets are our way to create open source templates for generating code for various languages to get started quickly with writing code that interacts with [SFTP To Go][home].

Every code snippet has three identifiers: `language`, `dependency` and `protocol`. 

* `language` of a code snippet is the programming language in which the code snippet is generated.
* `dependency` of a code snippet is the underlying library used by the language to establish a connection to SFTP To Go.
* `protocol` of a code snippet is the connection protocol used by the language to connect to SFTP To Go.

List of supported code snippets:

| Language | Dependency | Protocol |
|----------|------------|----------|
| Go | sfpt | SFTP |
| Node.js | ssh2 | SFTP |
| PHP | ssh2 | SFTP |
| PowerShell | post-ssh | SFTP |
| Python | py-sftp | SFTP |
| Ruby | net-sftp | SFTP |
| Shell | aws-cli | Amazon S3 |
| Shell | sftp-client | SFTP |

Every code snippet is stored as a [Mustache](https://mustache.github.io/) template to be able to render code snippets with SFTP To Go credentials as tags.

List of supported tags:

| Tag | Description |
|-----|-------------|
| UserName | The credentials user name |
| Password | The credentials password |
| Host | The credentials host name |
| URI | The credentials full URL |
| AccessKeyId | The AWS credentials access key ID |
| SecretAccessKey | The AWS credentials secret access key |
| Region | The AWS region |
| Bucket | The AWS bucket |

These tags can be used as placeholders for code snippet generators by SFTP To Go.

## Contributing

If you'd like to contribute, start by searching through the [issues][is] and [pull requests][pr] to see whether someone else has raised a similar idea or question.

If you don't see your idea listed, and you think it fits into the goals of this guide, open a pull request.

### Types of contributions

New code snippets: To add a new code snippet template, create a pull request with your new file. Since these code snippets are bundled with our app, they follow a particular structure for tags that can be used in the template as mentioned above.

Bug fixes: We'd be happy to accept fixes to known issues in any of the code snippets, as long it's a filed through the [issues][is].

### How to contribute

Once you've made your great commits:

1. [Fork][fk] SFTP To Go examples
2. Create a topic branch - `git checkout -b my_branch`
3. Push to your branch - `git push origin my_branch`
4. Create an [Issue][is] with a link to your branch
5. That's it! Our team will review the PR and merge 

Licensing
=========

See [LICENSE](LICENSE)

[home]: https://sftptogo.com/
[fk]: https://help.github.com/forking/
[is]: https://github.com/crazyantlabs/sftptogo-examples/issues
[pr]: https://github.com/crazyantlabs/sftptogo-examples/pulls