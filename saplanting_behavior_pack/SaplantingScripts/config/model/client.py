# -*- coding: utf-8 -*-
# @Time    : 2023/7/24 11:14
# @Author  : taokyla
# @File    : client.py

import mod.client.extraClientApi as clientApi

from .base import SavableConfig
from ...util.common import dealunicode, Singleton

compFactory = clientApi.GetEngineCompFactory()

configComp = compFactory.CreateConfigClient(clientApi.GetLevelId())


class ClientSavableConfig(SavableConfig):
    """
    客户端可保存配置基类，继承自 SavableConfig，使用单例模式保证全局唯一。
    负责从客户端配置组件读取和写入配置数据。
    """
    __metaclass__ = Singleton
    _ISGLOBAL = False

    def load(self):
        """
        从客户端配置组件读取配置信息，
        并通过 dealunicode 递归转换所有 unicode 字符串为 utf8 编码的字符串，
        最后调用 load_data 将数据载入当前实例。
        """
        data = dealunicode(configComp.GetConfigData(self._KEY, self._ISGLOBAL))
        if data:
            self.load_data(data)

    def save(self):
        """
        将当前配置实例的数据通过 dump() 序列化为 dict，
        然后保存到客户端配置组件。
        """
        configComp.SetConfigData(self._KEY, self.dump(), isGlobal=self._ISGLOBAL)
