# -*- coding: utf-8 -*-
import mod.server.extraServerApi as serverApi

from ..config.modConfig import *
from ..util.listen import Listen

engineName = serverApi.GetEngineNamespace()
engineSystem = serverApi.GetEngineSystemName()


class BaseServerSystem(serverApi.GetServerSystemCls()):
    ListenDict = {Listen.minecraft: (engineName, engineSystem), Listen.client: (ModName, ClientSystemName), Listen.server: (ModName, ServerSystemName)}

    def __init__(self, namespace, name):
        """
        初始化服务器系统，调用父类构造函数，获取当前关卡ID，
        并调用 onRegister 绑定监听函数。
        """
        super(BaseServerSystem, self).__init__(namespace, name)
        self.levelId = serverApi.GetLevelId()
        self.onRegister()

    def onRegister(self):
        """
        遍历自身所有方法，找出带有监听事件属性的方法，
        自动注册对应的事件监听。
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
        监听指定事件：
        根据事件类型从 ListenDict 获取对应系统名称和实例，
        调用系统接口 ListenForEvent 注册事件回调。
        """
        if _type not in self.ListenDict:
            return
        name, system = self.ListenDict[_type]
        self.ListenForEvent(name, system, event, self, func, priority=priority)

    def unlisten(self, event, func, _type=Listen.minecraft, priority=0):
        """
        取消监听指定事件：
        根据事件类型从 ListenDict 获取对应系统名称和实例，
        调用系统接口 UnListenForEvent 取消事件回调。
        """
        if _type not in self.ListenDict:
            return
        name, system = self.ListenDict[_type]
        self.UnListenForEvent(name, system, event, self, func, priority=priority)
