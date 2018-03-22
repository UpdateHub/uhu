# uhu - UpdateHub Utilities [![Build Status](https://travis-ci.org/updatehub/uhu.svg?branch=master)](https://travis-ci.org/updatehub/uhu) [![Coverage Status](https://coveralls.io/repos/github/UpdateHub/uhu/badge.svg?branch=master)](https://coveralls.io/github/UpdateHub/uhu?branch=master)

uhu is an interactive prompt and a command line utility to manage update
packages for [UpdateHub](https://github.com/UpdateHub/updatehub) agent.

## Installing

uhu is available in PyPI and can be install with `pip`:

```
pip3 install uhu
```

### System Dependencies

uhu is compatible with Python 3.4 and onwards.

If you plan to work with compressed data, be sure to also have
installed in your system the compressors you use.

Until now, UpdateHub supports the following compressors:

* lzop
* xz
* gzip


## Getting started

To start uhu interactive prompt, just type `uhu` in your
terminal. Within interactive prompt, you can always press `tab` to
autocomplete or to check available commands.

### Setting credentials

In the first run `uhu`, you will be prompted to provide your UpdateHub
credentials. You can get your access and secrete keys in UpdateHub web
interface.

After that you are ready to start creating update packages.

> You just have to do this step once, since uhu will save your
> credentials at `$HOME/.uhu`. If you need to update your credentials,
> you may use the `auth` command within interactive prompt.

## Creating an update package

To create a update package, we need to set some basic info first.

> The `show` command will always print your current package data so
> you can check if everything is ok.

### 1. Set the product

Currently, you can't create a new product within `uhu`, so you have to
first create a product in the web interface.

After that, grab the product UID generated and type the following
within the interactive prompt:

    product use <your-product-uid>

Your prompt will be updated with an abbreviated version of what you
typed. And remember, if you need to check if everything is ok, just
type `show`.

### 2. Set the package version

The package version plays a very important role within UpdateHub. This
version will be the software version that your device will run after
an update. To set it, just type:

    package version <the-new-version>

### 3. Set the hardware compatibility

By default, the package that you are creating will be available for
all type of hardware that you have. But if you have many devices in
field it is also possible that you also have different brands of
hardware for the same product. Taking this in consideration, it is
possible that, for example, hardware brand X requires an incompatible
configuration with hardware brand Y to update to version 2.0.

For this kind of issue, `uhu` presents a way to create an update
package to only selected hardware. To do so, just add the hardware
identifiers that are compatible with the package that you are
creating:

    hardware add

It will start a new prompt that will ask you to specify a hardware
identifier that you want to target with this package.

If you need to remove a hardware identifier, type the following:

    hardware remove

And you all be presented to a prompt that will assist you into remove
the identifiers that you want.

### 4. Add objects (files, images, firmwares, etc...)

With everything set, you are now able to add true content of your
updated package. Since this content may be diverse, from just an image
file to a complete root filesystem image, we like to call them as
objects.

To add an object to your package, type:

    package add

It will start a new prompt asking you all the needed information to
instruct the UpdateHub device agent on how to install the object
within your device.

There are also 2 more commands to help you to manage objects, `edit` and `remove`:

    package edit    # edit an already added object
    package remove  # remove an added object

### 5. Push the package

After to set product, version, supported hardware and objects, you are now able
to upload your package to the UpdateHub server. To do so:

    package push

It's done! You are now able to go to the UpdateHub web interface and
rollout your package.

## License

uhu is released under the GPL-2.0 license.
