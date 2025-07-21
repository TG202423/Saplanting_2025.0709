# -*- coding: utf-8 -*-
# @Time    : 2023/7/24 11:15
# @Author  : taokyla
# @File    : server.py
import mod.server.extraServerApi as serverApi

from .base import SavableConfig
from ...util.common import dealunicode, Singleton

compFactory = serverApi.GetEngineCompFactory()

extraDataComp = compFactory.CreateExtraData(serverApi.GetLevelId())


class ServerSavableConfig(SavableConfig):
    __metaclass__ = Singleton

    def load(self):
        """
        从服务器额外数据组件读取配置数据，
        使用 dealunicode 处理编码，
        并调用 load_data 加载数据。
        """
        data = dealunicode(extraDataComp.GetExtraData(self._KEY))
        if data:
            self.load_data(data)

    def save(self):
        """
        保存当前配置数据到服务器额外数据组件，
        通过 autoSave=True 自动保存，
        并显式调用 SaveExtraData 确保写入磁盘。
        """
        extraDataComp.SetExtraData(self._KEY, self.dump(), autoSave=True)
        extraDataComp.SaveExtraData()


class PlayerSavableConfig(SavableConfig):
    """
    针对单个玩家的可保存配置，管理玩家的专属配置数据。
    每个实例绑定一个 playerId。
    """
    def __init__(self, playerId):
        self._playerId = playerId
        self._extraDataComp = compFactory.CreateExtraData(playerId)

    @property
    def playerId(self):
        """
        返回当前实例关联的玩家ID
        """
        return self._playerId

    def load(self):
        """
        读取当前玩家的额外数据，
        处理编码后调用 load_data 加载。
        """
        data = dealunicode(self._extraDataComp.GetExtraData(self._KEY))
        if data:
            self.load_data(data)

    def save(self):
        """
        保存当前玩家配置数据，
        自动保存并调用 SaveExtraData 确保写入。
        """
        self._extraDataComp.SetExtraData(self._KEY, self.dump(), autoSave=True)
        self._extraDataComp.SaveExtraData()
