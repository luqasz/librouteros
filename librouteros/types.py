# -*- coding: UTF-8 -*-

from typing import (
    Dict,
    Iterator,
    Any,
    List,
    AsyncGenerator,
)

ReplyDict = Dict[str, Any]
ResponseIter = Iterator[ReplyDict]
AsyncResponseIter = AsyncGenerator[ReplyDict, None]
QueryGen = Iterator[str]
Response = List[Dict[str, Any]]
