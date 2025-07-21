# -*- coding: utf-8 -*-

import mod.client.extraClientApi as clientApi
import mod.server.extraServerApi as serverApi
from mod.common.mod import Mod

from .config.modConfig import *


@Mod.Binding(name=ModName, version=ModVersion)
class SaplantingMod(object):

    def __init__(self):
        pass

    @Mod.InitServer()
    def server_init(self):
        """
        将服务器系统注册到引擎中
        """
        serverApi.RegisterSystem(ModName, ServerSystemName, ServerSystemClsPath)

    @Mod.InitClient()
    def client_init(self):
        """
        将客户端系统注册到引擎中
        """
        clientApi.RegisterSystem(ModName, ClientSystemName, ClientSystemClsPath)

    @Mod.DestroyClient()
    def destroy_client(self):
        """
        退出客户端时进行清理工作
        """
        pass

    @Mod.DestroyServer()
    def destroy_server(self):
        """
        关闭服务器时进行清理工作
        """
        pass
