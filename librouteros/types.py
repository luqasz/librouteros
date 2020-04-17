# -*- coding: UTF-8 -*-

from typing import (
    Dict,
    Iterator,
    Any,
)

ReplyDict = Dict[str, Any]
ResponseIter = Iterator[ReplyDict]
QueryGen = Iterator[str]
