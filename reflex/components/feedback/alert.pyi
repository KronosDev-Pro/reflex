"""Stub file for alert.py"""
# ------------------- DO NOT EDIT ----------------------
# This file was generated by `scripts/pyi_generator.py`!
# ------------------------------------------------------

from typing import Union, overload, Optional
from reflex.components.libs.chakra import ChakraComponent
from reflex.components.component import Component
from reflex.vars import Var, BaseVar, ComputedVar
from reflex.event import EventChain

class Alert(ChakraComponent):
    @overload
    @classmethod
    def create(cls, *children, icon, title, desc, status: Optional[Union[Var[str], str]] = None, variant: Optional[Union[Var[str], str]] = None, **props) -> "Alert": ...  # type: ignore

class AlertIcon(ChakraComponent):
    @overload
    @classmethod
    def create(cls, *children, **props) -> "AlertIcon": ...  # type: ignore

class AlertTitle(ChakraComponent):
    @overload
    @classmethod
    def create(cls, *children, **props) -> "AlertTitle": ...  # type: ignore

class AlertDescription(ChakraComponent):
    @overload
    @classmethod
    def create(cls, *children, **props) -> "AlertDescription": ...  # type: ignore