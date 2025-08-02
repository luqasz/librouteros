# -*- coding: UTF-8 -*-

from typing import (
    Any,
    AsyncGenerator,
    Dict,
    Iterator,
    List,
)

ReplyDict = Dict[str, Any]
ResponseIter = Iterator[ReplyDict]
AsyncResponseIter = AsyncGenerator[ReplyDict, None]
QueryGen = Iterator[str]
Response = List[Dict[str, Any]]
