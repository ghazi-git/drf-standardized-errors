# FAQs

## Standardized errors are not shown in local development

By default, standardized error responses when `DEBUG=True` for unhandled exceptions are disabled.
That is to allow you to get more information out of the traceback. You can enable standardized errors
instead with:

```python
DRF_STANDARDIZED_ERRORS = {"ENABLE_IN_DEBUG_FOR_UNHANDLED_EXCEPTIONS": True}
```


## Some exceptions are not converted to the standardized format

This package is a DRF exception handler, so it only standardizes errors that reach a DRF API view.
That means it cannot handle errors that happen at the middleware level for example. To handle those
as well, you can customize the necessary [django error views](https://docs.djangoproject.com/en/dev/topics/http/views/#customizing-error-views).
You can find more about that in [this issue](https://github.com/ghazi-git/drf-standardized-errors/issues/44).


## I want to let exceptions propagate up the middleware stack

This might be needed when code written in middleware adds custom logic based on raised exceptions
(either by you or by a third party package). In that case, it is possible to allow the exception
to pass through the DRF exception handler and later convert it to the corresponding error response
in django error views. You can check [this issue](https://github.com/ghazi-git/drf-standardized-errors/issues/91#issuecomment-2397956441) for sample code.


## How can I add extra details about the exception in the error response

This can be done using a custom exception along with a custom exception formatter. You can find sample
code in [this issue](https://github.com/ghazi-git/drf-standardized-errors/issues/95#issuecomment-2661633736).
Note that this does not work with `ValidationError`s or its subclasses raised in a serializer. That's
because DRF creates new `ValidationError` instances when they are raised. See
[here](https://github.com/encode/django-rest-framework/blob/f30c0e2eedda410a7e6a0d1b351377a9084361b4/rest_framework/serializers.py#L221-L231)
and [here](https://github.com/encode/django-rest-framework/blob/f30c0e2eedda410a7e6a0d1b351377a9084361b4/rest_framework/serializers.py#L443-L448).


## How to integrate this package with djangorestframework-camel-case

You can check this [issue](https://github.com/ghazi-git/drf-standardized-errors/issues/59#issuecomment-1889826918)
for a possible solution. Still, `djangorestframework-camel-case` is built to work specifically with
the default exception handler from DRF. It assumes that field names are the keys in the returned dict.
So, that does not work well with this package.
