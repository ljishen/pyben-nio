#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import abc
import logging
import re
import typing


class IOFilter(abc.ABC):
    """Abstrct base class of all the methods of how to read data from file.

    Args:
        file_obj (typing.BinaryIO): The file object to read from.
        **kwargs: Extra parameters for specific method.

    """

    logger = logging.getLogger(__name__)

    def __init__(
            self,
            file_obj: typing.BinaryIO,
            **kwargs) -> None:
        self.file_obj = file_obj
        self.kwargs = kwargs

    @abc.abstractmethod
    def read(self, size: int) -> bytes:
        """Read and return up to size bytes.

        Args:
            size (int): It must be greater than 0. Note that multiple
                underlying reads may be issued to satisfy the byte count.

        """
        if size is None or size <= 0:
            err = ValueError("read size must be > 0")
            self._log_and_exit(err)

    @classmethod
    def create(
            cls: typing.Type['IOFilter'],
            file_obj: typing.BinaryIO,
            extra_args: typing.List[str]) -> 'IOFilter':
        """Create specific class instance.

        Args:
            cls (typing.Type['IOFilter']): The class itself. See the type hints
                for the class itself on https://stackoverflow.com/a/44664064
            file_obj (typing.BinaryIO): The first parameter in the constructor.
            extra_args (typing.List[str]): The remaining optional parameters
                in strings to be passed in the constructor.

        Returns:
            'IOFilter': See why we can only use string instead of the
                class itself on https://stackoverflow.com/a/33533514

        """
        extra_args_dict = {}  # type: typing.Dict[str, str]
        for item in extra_args:
            pair = re.split('[:=]', item, maxsplit=1)
            if len(pair) < 2:
                err = ValueError("Invalid method argument: " + str(pair))
                cls.logger.error(str(err))
                raise err

            extra_args_dict[pair[0]] = pair[1]

        cls.logger.info("[method: %s] [input parameters: %s]",
                        cls.__module__, extra_args_dict)

        method_params = cls._get_method_params()
        kwargs = {}  # type: typing.Dict[str, typing.Union[str, int]]
        for n, f in method_params.items():
            input_v = extra_args_dict.pop(n, '')
            if not input_v:
                err = ValueError(
                    "Required method parameter '%s' not found." % n)
                cls._log_and_exit(err)

            kwargs[n] = f(input_v)

        if extra_args_dict:
            err = ValueError(
                "Unknow extra method paramsters %s" % extra_args_dict)
            cls._log_and_exit(err)

        return cls(file_obj, **kwargs)

    @classmethod
    @abc.abstractmethod
    def _get_method_params(cls: typing.Type['IOFilter']) -> typing.Dict[
            str, typing.Callable[[str], typing.Union[str, int]]]:
        """Return required method parameters in dictionary.

        For each item in the return dictionary, the key is the name of the
        parameter, and the value is a function to convert the input value
        in string into the necessary type used in the program.

        """

    @classmethod
    def _log_and_exit(
            cls: typing.Type['IOFilter'],
            err: Exception) -> None:
        cls.logger.error(str(err))
        raise err

    @classmethod
    def print_desc(cls: typing.Type['IOFilter']) -> None:
        """Print information about method initialization."""
        print('-' * 80)
        print('[MODULE] ' + cls.__module__)
        print('-' * 80)
        print('[DESC]   ' + str(cls.__doc__))

        method_params = cls._get_method_params()
        if method_params:
            print('[PARAMS] Extra method parameter', method_params)
        else:
            print('[PARAMS] Extra method parameter is not required.')
