# -*- coding: UTF-8 -*-

from collections.abc import AsyncGenerator, Iterator
from typing import Union

ROSType = Union[str, int, bool]
ReplyDict = dict[str, ROSType]
ResponseIter = Iterator[ReplyDict]
AsyncResponseIter = AsyncGenerator[ReplyDict]
Response = list[ReplyDict]
QueryGen = Iterator[str]
