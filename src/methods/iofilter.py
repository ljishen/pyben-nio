#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from inspect import getfullargspec
from io import BufferedIOBase
from socket import socket

import abc
import logging
import re
import typing
import textwrap

from util import Util

LINE_WIDTH = 79


class MethodParam(object):
    """Simple object for storing method related parameters."""

    logger = logging.getLogger(__name__)

    ParamValue = typing.Any
    ParamConverter = typing.Callable[[str], ParamValue]

    _WHITESPACE_REGEX = re.compile(r'\s+', re.ASCII)

    def __init__(
            self: 'MethodParam',
            name: str,
            conv: ParamConverter,
            desc: str,
            default: str = None) -> None:
        """Initialize instance for this class.

        Args:
            name (str): Name of the method parameter.
            conv (ParamConverter): A function for converting string to the
                object of desired type (ParamValue).
            desc (str): The description/help message of this parameter.
            default (str): The default value of this parameter.

        """
        self.name = name
        self.__conv = conv
        self.__desc = desc
        self.__default = default

    def get_value(self: 'MethodParam', string: str) -> 'ParamValue':
        """Convert string to the object of desired type using the converter.

        Returns:
            ParamValue: A converted object if the string is not empty and
                not None, otherwise the default value.

        """
        if not string:
            if self.__default is None:
                raise ValueError(
                    "Required method parameter '%s' not found" % self.name)

            string = self.__default

        return self.__conv(string)

    def __str__(self: 'MethodParam'):
        """Generate nicely printable string representation for this object."""
        try:
            return_type = getfullargspec(self.__conv).annotations['return']
        except (KeyError, TypeError):
            self.logger.debug(
                "Fallback to show the type of function '%s' because the \
return type is unavailable", self.__conv)
            return_type = self.__conv

        optional_tag = 'Optional. ' if self.__default is not None else ''
        clean_desc = optional_tag + \
            self._WHITESPACE_REGEX.sub(' ', self.__desc).strip()

        text = "{} ({}): {}{}".format(
            self.name,
            return_type,
            clean_desc,
            ' (Default: {})'.format(self.__default) if self.__default else '')

        return textwrap.fill(text,
                             LINE_WIDTH,
                             initial_indent=' ' * 4,
                             subsequent_indent=' ' * 8)


T = typing.TypeVar('T', BufferedIOBase, socket)


class IOFilter(typing.Generic[T]):
    """ABC of all the methods of how to read data from the underlying stream.

    Args:
        stream (T): The underlying stream to read data from.
        **kwargs: Extra parameters for specific method.

    """

    logger = logging.getLogger(__name__)

    def __init__(
            self: 'IOFilter[T]',
            stream: T,
            bufsize: int,
            **kwargs) -> None:
        """Initialize base attributes for all subclasses."""
        self._stream = stream  # type: T
        self.kwargs = kwargs
        self._buffer = bytearray(self._get_bufarray_size(bufsize))
        self.__count = 0

    @abc.abstractmethod
    def read(self: 'IOFilter[T]', size: int) -> typing.Tuple[bytes, int]:
        """Read and return up to size bytes.

        Args:
            size (int): It must be greater than 0. Note that multiple
                underlying reads may be issued to satisfy the byte count.

        Returns:
            typing.Tuple[bytes, int]: The result bytes and a control number
                that associates with the bytes.

        """
        if size is None or size <= 0:
            err = ValueError("Read size must be > 0")
            Util.log_and_raise(self.logger, err)

        return (bytes(), 0)

    def get_count(self: 'IOFilter[T]') -> int:
        """Get the total number of raw bytes have read."""
        return self.__count

    def close(self: 'IOFilter[T]') -> None:
        """Close associated resources."""
        self._stream.close()

    def _get_bufarray_size(self: 'IOFilter[T]', bufsize: int) -> int:
        """Return the size to be used to create the buffer bytearray.

        Returns:
            int: Return the bufsize by default.

        """
        return bufsize

    def _get_or_create_bufview(self: 'IOFilter[T]') -> memoryview:
        """Return the memoryview for the bytearray buffer."""
        if not hasattr(self, '_bufview'):
            # pylint: disable=attribute-defined-outside-init
            self._bufview = memoryview(self._buffer)
        return self._bufview

    def _incr_count(self: 'IOFilter[T]', num: int) -> None:
        """Add num to the total number of raw bytes."""
        self.__count += num

    @classmethod
    def create(
            cls: typing.Type['IOFilter[T]'],
            stream: T,
            bufsize: int,
            extra_args: typing.List[str]) -> 'IOFilter[T]':
        """Create an instance of a subclass.

        Args:
            cls (typing.Type['IOFilter[T]']): The class object itself. See the
                type hints for the class itself on
                https://stackoverflow.com/a/44664064
            stream (T): The first parameter in the constructor.
            extra_args (typing.List[str]): The remaining optional parameters
                in a list of strings to be passed in the constructor.

        Returns:
            'IOFilter[T]': See why we can only use string instead of the
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

            extra_args_dict[pair[0].strip()] = pair[1].strip()

        cls.logger.info("[method: %s] [method parameters: %s]",
                        cls.__module__, extra_args_dict)

        method_params = cls._get_method_params()

        kwargs = {}  # type: typing.Dict[str, MethodParam.ParamValue]

        for paramobj in method_params:
            input_v = extra_args_dict.pop(paramobj.name, '')
            try:
                kwargs[paramobj.name] = paramobj.get_value(input_v)
            except ValueError as err:
                Util.log_and_raise(cls.logger, err)

        if extra_args_dict:
            Util.log_and_raise(
                cls.logger,
                ValueError("Unknow extra method paramsters %s"
                           % extra_args_dict))

        return cls(stream, bufsize, **kwargs)

    @classmethod
    def _get_method_params(cls: typing.Type['IOFilter[T]']) -> typing.List[
            MethodParam]:
        """Return method parameters as a list.

        Subclass should override this method if extra parameters are needed.

        """
        return []

    @classmethod
    def print_desc(cls: typing.Type['IOFilter[T]']) -> None:
        """Print information about method initialization."""
        separator = '-' * LINE_WIDTH

        print(separator)
        print('[MODULE] ' + cls.__module__)
        print(separator)

        print('[DESC] ' + str(cls.__doc__))

        method_params = cls._get_method_params()
        if method_params:
            print('[PARAMS] ')
            for paramobj in method_params:
                print(paramobj)
        else:
            print('[PARAMS] Extra method parameter is not required.')

        print(separator)
