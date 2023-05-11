### 2023-05-11 Version 0.3.2
* Fix: solve ImportError that urllib3 v2.0 only supports OpenSSL 1.1.1+.

### 2023-03-27 Version 0.3.1
* Fix: allow retry when retry_times equals 0.

### 2022-10-20 Version 0.3.0
* Return more detail in error info.

### 2022-04-21 Version 0.2.9
* Support certificates.

### 2021-07-27 Version 0.2.8
* Remove local modules & Fix some no-module errors.
* Update some config.

### 2021-04-27 Version 0.2.7
* Throw TeaException will not retry.
* Improve instance check of stream.

### 2021-03-17 Version 0.2.6
* Improve TeaModel to avoid serialization exception.

### 2021-03-15 Version 0.2.5
* The `do_action` method uses a connection pool.
* Improve UnretryableException.

### 2021-01-28 Version 0.2.4
* Retry is not allowed by default.

### 2021-01-08 Version 0.2.3
* Aiohttp included in the Tea module.

### 2020-12-16 Version 0.2.2
* async_do_action method supports parsing stream.

### 2020-12-14 Version 0.2.1
* Fix bug that the error message is not printed when throw UnretryableException.

### 2020-12-07 Version 0.2.0
* Drop support for python3.4.
* Drop support for python3.5.
* Added support for python3.9.
* Improve TeaException error message.
* Support async do action.

### 2020-10-30 Version 0.1.5

* Add to_map & from_map methods.

### 2020-09-24 Version 0.1.4

* Improve the message of failed model verification.

### 2020-09-18 Version 0.1.3

* Print debugging information in debug mode when configuring DEBUG environment variables.

### 2020-09-02 Version 0.1.2

* Fix string format.

### 2020-08-27 Version 0.1.1

* Add readable & writable.
* Improve exception message.

### 2020-08-21 Version 0.1.0

* Improve model compatibility.

### 2020-08-03 Version 0.0.9

* Support Bytes IO

### 2020-07-20 Version 0.0.8

* Improve combination url.
* Improve install requires library version.

### 2020-07-13 Version 0.0.7

* Fixed compose_url to get correct rpc signature

### 2020-07-10 Version 0.0.6

* Fixed type error when concatenating strings

### 2020-06-22 Version 0.0.5
* Supported python 3.4

### 2020-05-21 Version 0.0.4
* Supported ignore ssl
* Supported http proxy
* Supported https proxy

### 2020-05-21 Version 0.0.3
* Support merge TeaModel
* Add BaseStream class

### 2020-05-15 Version 0.0.2
* Supported generator and util

### 2020-03-26 Version 0.0.1
* First release