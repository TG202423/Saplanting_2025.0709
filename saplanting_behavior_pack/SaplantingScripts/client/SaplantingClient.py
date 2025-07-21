# -*- coding: utf-8 -*-
from random import random

import mod.client.extraClientApi as clientApi

from .BaseClientSystem import BaseClientSystem
from ..config.heyconfig import ClientSetting
from ..config.sapling import default_saplings
from ..util.common import Singleton
from ..util.listen import Listen

compFactory = clientApi.GetEngineCompFactory()
engineName = clientApi.GetEngineNamespace()
engineSystem = clientApi.GetEngineSystemName()


class ClientMasterSetting(object):
    """
    树苗掉落等待与检测配置（客户端保存的一些参数）
    """
    __metaclass__ = Singleton
    wait_time_range = 5
    check_time_range = 15

    def __init__(self):
        """
        初始树苗列表（元组表示物品名和附加值）
        """
        self.saplings = default_saplings
        self.min_wait_time = 3
        self.check_min_wait_time = 15 + self.min_wait_time

    def load_config(self, data):
        """
        从服务端传输的数据中加载设定（通常在游戏开始同步）
        """
        if "saplings" in data:
            self.saplings = set(tuple(value) for value in data["saplings"])
        if "min_wait_time" in data:
            self.min_wait_time = max(0, data["min_wait_time"])
            self.check_min_wait_time = 15 + self.min_wait_time

    def get_wait_time(self):
        """
        获取随机等待时间（种植树苗前等待）
        """
        return random() * self.wait_time_range + self.min_wait_time

    def get_check_wait_time(self):
        """
        获取随机检测时间（检查实体是否在地面上）
        """
        return random() * self.check_time_range + self.check_min_wait_time


class SaplantingClient(BaseClientSystem):
    """
    树苗掉落客户端系统：监听实体掉落事件、地面碰撞事件等，并向服务端通知处理。
    """
    def __init__(self, namespace, name):
        super(SaplantingClient, self).__init__(namespace, name)
        self.game_comp = compFactory.CreateGame(self.levelId)
        self.master_setting = ClientMasterSetting()
        self.item_entities = {}
        self.client_setting = ClientSetting()

    @Listen.on("LoadClientAddonScriptsAfter")
    def on_enabled(self, event=None):
        """
        客户端插件脚本加载完成后，加载客户端配置
        """
        self.client_setting.load()
        comp = clientApi.CreateComponent(self.levelId, "HeyPixel", "Config")
        if comp:
            from ..config.heyconfig import register_config
            comp.register_config(register_config)

    @Listen.on("UiInitFinished")
    def on_local_player_stop_loading(self, event=None):
        """
        本地玩家加载完成后，将本地配置（如是否砍树）同步给服务器
        """
        self.NotifyToServer("SyncPlayerTreeFallingState", {"playerId": self.playerId, "state": self.client_setting.tree_felling})

    def reload_client_setting(self):
        """
        重新加载本地配置并通知服务器状态变更
        """
        self.client_setting.load()
        self.NotifyToServer("SyncPlayerTreeFallingState", {"playerId": self.playerId, "state": self.client_setting.tree_felling})

    @Listen.server("SyncMasterSetting")
    def on_sync_master_setting(self, data):
        """
        从服务器同步主配置（如树苗白名单、检测时间）
        """
        self.master_setting.load_config(data)

    @Listen.on("AddEntityClientEvent")
    def on_add_sapling_item(self, event):
        """
        掉落物生成后，判断其是否在树苗白名单内，若存在则加入监听范围
        """
        # todo 已知event的文档如右侧连接 ：    https://mc.163.com/dev/mcmanual/mc-dev/mcdocs/1-ModAPI/%E4%BA%8B%E4%BB%B6/%E4%B8%96%E7%95%8C.html?key=AddEntityClientEvent&docindex=2&type=0
        # todo 已存在 self.master_setting.saplings 为树苗的枚举

        entityId = event["id"]
        if entityId not in self.item_entities:
            item_key = (event["itemName"], event["auxValue"])
            if item_key in self.master_setting.saplings:
                self.item_entities[entityId] = item_key
                self.game_comp.AddTimer(self.master_setting.get_check_wait_time(), self.check_on_ground, entityId)

    @Listen.on("RemoveEntityClientEvent")
    def on_remove_entity(self, event):
        """
        实体移除时，从监控列表中移除（防止冗余检测）
        """
        entityId = event["id"]
        if entityId in self.item_entities:
            self.item_entities.pop(entityId)

    @Listen.on("OnGroundClientEvent")
    def on_sapling_on_ground(self, event):
        """
        实体落地事件，若该实体是我们监控的树苗，则在延迟后通知服务端
        """
        entityId = event["id"]
        if entityId in self.item_entities:
            self.game_comp.AddTimer(self.master_setting.get_wait_time(), self.on_ground_notify, entityId)

    def on_ground_notify(self, entityId):
        """
        实体落地后的通知事件，发送树苗信息到服务器（触发种植逻辑）
        """
        if entityId in self.item_entities:
            itemName, auxValue = self.item_entities[entityId]
            # print "notify sapling item on ground", entityId
            self.NotifyToServer("onSaplingOnGround", {"playerId": self.playerId, "entityId": entityId, "itemName": itemName, "auxValue": auxValue})

    def check_on_ground(self, entityId):
        """
        定时检查实体是否落地，若落地则立即通知服务端；否则继续延迟检查。
        """
        if entityId in self.item_entities:
            if compFactory.CreateAttr(entityId).isEntityOnGround():
                self.on_ground_notify(entityId)
            else:
                self.game_comp.AddTimer(self.master_setting.get_check_wait_time(), self.check_on_ground, entityId)

    def reload_master_setting(self):
        """
        向服务器请求重新加载主配置（可能由管理员发起）
        """
        self.NotifyToServer("ReloadMasterSetting", {})
