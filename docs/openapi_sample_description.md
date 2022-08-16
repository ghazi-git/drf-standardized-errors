# Sample API Description

Check the [Tips and Tricks](openapi.md#hide-error-responses-that-show-in-every-operation) to understand how to use this sample API description.

## Overview
Here you will probably give an overview of the API and add a description for it.

## Authentication
Since the API requires authentication, you might want to add a section to describe the authentication flow as well.

## Errors
Now this is the important section in this example. In this section, you can list the error responses that appear
in every operation with some explanation. It can go sth like:

### 401 Unauthorized
These errors are returned with the status code 401 whenever the authentication fails or a request is made to an
endpoint without providing the authentication information as part of the request. Here are the 2 possible errors
that can be returned.
```json
{
    "type": "client_error",
    "errors": [
        {
            "code": "authentication_failed",
            "detail": "Incorrect authentication credentials.",
            "attr": null
        }
    ]
}
```
```json
{
    "type": "client_error",
    "errors": [
        {
            "code": "not_authenticated",
            "detail": "Authentication credentials were not provided.",
            "attr": null
        }
    ]
}
```

### 405 Method Not Allowed
This is returned when an endpoint is called with an unexpected http method. For example, if updating a user requires
a POST request and a PATCH is issued instead, this error is returned. Here's how it looks like:

```json
{
    "type": "client_error",
    "errors": [
        {
            "code": "method_not_allowed",
            "detail": "Method “patch” not allowed.",
            "attr": null
        }
    ]
}
```

### 406 Not Acceptable
This is returned if the `Accept` header is submitted and contains a value other than `application/json`. Here's how the response would look:

```json
{
    "type": "client_error",
    "errors": [
        {
            "code": "not_acceptable",
            "detail": "Could not satisfy the request Accept header.",
            "attr": null
        }
    ]
}
```

### 415 Unsupported Media Type
This is returned when the request content type is not json. Here's how the response would look:

```json
{
    "type": "client_error",
    "errors": [
        {
            "code": "not_acceptable",
            "detail": "Unsupported media type “application/xml” in request.",
            "attr": null
        }
    ]
}
```

### 500 Internal Server Error
This is returned when the API server encounters an unexpected error. Here's how the response would look:

```json
{
    "type": "server_error",
    "errors": [
        {
            "code": "error",
            "detail": "A server error occurred.",
            "attr": null
        }
    ]
}
```
