#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from inspect import getfullargspec

import abc
import logging
import re
import typing


class IOFilter(abc.ABC):
    """Abstrct base class of all the methods of how to read data from file.

    Args:
        file_obj (typing.BinaryIO): The file object to read from.

    """

    logger = logging.getLogger(__name__)

    def __init__(self, file_obj: typing.BinaryIO) -> None:
        self.file_obj = file_obj

    @abc.abstractmethod
    def read(self, size: int=-1) -> bytes:
        """Read and return up to size bytes.

        Args:
            size (int): If the argument is omitted, None, or negative, data is
                read and returned until EOF is reached. An empty bytes object
                is returned if the stream is already at EOF. If the argument is
                positive, multiple raw reads may be issued to satisfy the byte
                count (unless EOF is reached first).

        """

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
        cls.logger.info("[method: %s]", cls.__module__)

        extra_args_dict = {}  # type: typing.Dict[str, str]
        for item in extra_args:
            pair = re.split('[:=]', item, maxsplit=1)
            if len(pair) < 2:
                err = ValueError("Invalid method argument: " + str(pair))
                cls.logger.error(str(err))
                raise err

            extra_args_dict[pair[0]] = pair[1]

        cls.logger.info("Method parameters: " + str(extra_args_dict))

        # Get the parameter names of the class constructor but
        # omit the first and second one -- the self and file_obj.
        constr_param_names = getfullargspec(cls.__init__)[0][2:]

        return cls._create(
            constr_param_names,
            file_obj,
            extra_args_dict)

    @staticmethod
    @abc.abstractmethod
    def _create(
            constr_param_names: typing.List[str],
            file_obj: typing.BinaryIO,
            extra_args_dict: typing.Dict[str, str]) -> 'IOFilter':
        """Create specific class instance.

        Args:
            constr_param_names (typing.List[str]): The necessary constructor
                parameters starting from the third one.
            file_obj (typing.BinaryIO): The first parameter in the constructor.
            extra_args_dict (typing.Dict[str, str]): The remaining optional
                parameters in key-value pairs to be passed in the
                constructor.

        Returns:
            'IOFilter': See why we can only use string instead of the
                class itself on https://stackoverflow.com/a/33533514

        """

    @staticmethod
    def _log_and_exit(err: Exception) -> None:
        logging.error(str(err))
        raise err

    @staticmethod
    @abc.abstractmethod
    def print_desc() -> None:
        """Print information about method initialization."""
