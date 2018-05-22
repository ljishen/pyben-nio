#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from inspect import getfullargspec

import abc
import logging
import re
import typing

_T = typing.TypeVar('_T')
_MethodParam = typing.Union[str, int, typing.Callable]


class IOFilter(typing.Generic[_T]):
    """ABC of all the methods of how to read data from the underlying stream.

    Args:
        stream (_T): The underlying stream to read data from.
        **kwargs: Extra parameters for specific method.

    """

    logger = logging.getLogger(__name__)

    def __init__(
            self: 'IOFilter[_T]',
            stream: _T,
            **kwargs) -> None:
        self.stream = stream
        self.kwargs = kwargs

    @abc.abstractmethod
    def read(self, size: int) -> bytes:
        """Read and return up to size bytes.

        Args:
            size (int): It must be greater than 0. Note that multiple
                underlying reads may be issued to satisfy the byte count.

        """
        if size is None or size <= 0:
            err = ValueError("Read size must be > 0")
            self._log_and_exit(err)

        return bytes()

    @classmethod
    def create(
            cls: typing.Type['IOFilter[_T]'],
            stream: _T,
            extra_args: typing.List[str]) -> 'IOFilter[_T]':
        """Create an instance of a subclass.

        Args:
            cls (typing.Type['IOFilter[_T]']): The class object itself. See the
                type hints for the class itself on
                https://stackoverflow.com/a/44664064
            stream (_T): The first parameter in the constructor.
            extra_args (typing.List[str]): The remaining optional parameters
                in a list of strings to be passed in the constructor.

        Returns:
            'IOFilter[_T]': See why we can only use string instead of the
                class itself on
                https://stackoverflow.com/a/33533514
                and
                https://www.python.org/dev/peps/pep-0484/#forward-references

        """
        extra_args_dict = {}  # type: typing.Dict[str, str]
        for item in extra_args:
            pair = re.split('[:=]', item, maxsplit=1)
            if len(pair) < 2:
                err = ValueError("Invalid method argument: " + str(pair))
                cls.logger.error(str(err))
                raise err

            extra_args_dict[pair[0]] = pair[1].strip()

        cls.logger.info("[method: %s] [input parameters: %s]",
                        cls.__module__, extra_args_dict)

        method_params = cls._get_method_params()

        kwargs = {}  # type: typing.Dict[str, _MethodParam]

        for n, cf in method_params.items():
            input_v = extra_args_dict.pop(n, '')
            if not input_v:
                err = ValueError(
                    "Required method parameter '%s' not found" % n)
                cls._log_and_exit(err)

            kwargs[n] = cf(input_v)

        if extra_args_dict:
            err = ValueError(
                "Unknow extra method paramsters %s" % extra_args_dict)
            cls._log_and_exit(err)

        return cls(stream, **kwargs)

    @classmethod
    @abc.abstractmethod
    def _get_method_params(cls: typing.Type['IOFilter[_T]']) -> typing.Dict[
            str,
            typing.Callable[[str], _MethodParam]]:
        """Return required method parameters in dictionary.

        For each item in the return dictionary, the key is the name of the
        parameter, and the value is a function to convert the input value
        in string into the necessary type used in the program.

        """

    @classmethod
    def _log_and_exit(
            cls: typing.Type['IOFilter[_T]'],
            err: Exception) -> None:
        cls.logger.error(str(err))
        raise err

    @classmethod
    def print_desc(cls: typing.Type['IOFilter[_T]']) -> None:
        """Print information about method initialization."""
        separator = '-' * 79
        print(separator)
        print('[MODULE] ' + cls.__module__)
        print(separator)

        print('[DESC]   ' + str(cls.__doc__))

        method_params = cls._get_method_params()

        name2rettypes = {}  # type: typing.Dict[str, _MethodParam]

        for param_name, func in method_params.items():
            try:
                return_type = getfullargspec(func).annotations['return']
            except (KeyError, TypeError):
                cls.logger.debug(
                    "Fallback to show the type of function '%s' because the \
return type is unavailable", func)
                return_type = func
                pass

            name2rettypes[param_name] = return_type

        if name2rettypes:
            print('[PARAMS] Extra method parameter', name2rettypes)
        else:
            print('[PARAMS] Extra method parameter is not required.')

        print(separator)
