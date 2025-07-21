# -*- coding: utf-8 -*-
import mod.client.extraClientApi as clientApi

from ..config.modConfig import *
from ..util.listen import Listen

engineName = clientApi.GetEngineNamespace()
engineSystem = clientApi.GetEngineSystemName()


class BaseClientSystem(clientApi.GetClientSystemCls()):
    ListenDict = {Listen.minecraft: (engineName, engineSystem), Listen.client: (ModName, ClientSystemName), Listen.server: (ModName, ServerSystemName)}

    def __init__(self, namespace, name):
        """
        构造函数，初始化系统的命名空间和名称，并注册各类事件监听器。
        """
        super(BaseClientSystem, self).__init__(namespace, name)
        self.levelId = clientApi.GetLevelId()
        self.playerId = clientApi.GetLocalPlayerId()
        self.onRegister()

    def onRegister(self):
        """
        在当前对象中遍历所有属性名，对于每个属性，如果它是一个可调用对象且拥有listen_event属性，
        则取出该方法的三个属性 listen_event、listen_type、listen_priority，
        然后调用 self.listen() 方法，注册该方法作为对应事件的监听器。
        """
        for key in dir(self):
            obj = getattr(self, key)
            if callable(obj) and hasattr(obj, 'listen_event'):
                event = getattr(obj, "listen_event")
                _type = getattr(obj, "listen_type")
                priority = getattr(obj, "listen_priority")
                self.listen(event, obj, _type=_type, priority=priority)

    def listen(self, event, func, _type=Listen.minecraft, priority=0):
        """
        首先判断事件是否在监听事件字典中，
        如果存在则获取当前系统名和实例标识
        并调用系统提供的 ListenForEvent 方法进行监听器注册。
        """
        if _type not in self.ListenDict:
            return
        name, system = self.ListenDict[_type]
        self.ListenForEvent(name, system, event, self, func, priority=priority)

    def unlisten(self, event, func, _type=Listen.minecraft, priority=0):
        """
        关闭某个事件的监听器。
        """
        if _type not in self.ListenDict:
            return
        name, system = self.ListenDict[_type]
        self.UnListenForEvent(name, system, event, self, func, priority=priority)
