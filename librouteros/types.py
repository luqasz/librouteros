# -*- coding: UTF-8 -*-

from typing import (
    Dict,
    Iterator,
    Any,
    List,
)

ReplyDict = Dict[str, Any]
ResponseIter = Iterator[ReplyDict]
QueryGen = Iterator[str]
Response = List[Dict[str, Any]]
