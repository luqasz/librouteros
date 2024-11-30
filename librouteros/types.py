# -*- coding: UTF-8 -*-

from typing import (
    Any,
    Dict,
    Iterator,
    List,
)

ReplyDict = Dict[str, Any]
ResponseIter = Iterator[ReplyDict]
QueryGen = Iterator[str]
Response = List[Dict[str, Any]]
