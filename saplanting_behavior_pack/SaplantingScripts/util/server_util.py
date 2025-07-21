# -*- coding: utf-8 -*-
# @Time    : 2023/10/31 13:29
# @Author  : taokyla
# @File    : server_util.py
from copy import deepcopy

import mod.server.extraServerApi as serverApi
from mod.common.minecraftEnum import ItemPosType

compFactory = serverApi.GetEngineCompFactory()      #获取引擎组件工厂，用于创建游戏中各种组件（物品、实体等）
itemComp = compFactory.CreateItem(serverApi.GetLevelId())       # 创建一个物品组件实例，用于获取物品信息

cachedItemInfos = {}    #存储物品信息的字典


def GetItemInfo(itemName, auxValue, isEnchanted=False):
    """
    判断字典中是否已经存入物品信息，没有就获取物品信息并存入
    :param itemName: 物品名称
    :param auxValue: 物品附加值
    :param isEnchanted: 是否附魔
    :return: 物品信息字典
    """
    key = (itemName, auxValue, isEnchanted)
    if key in cachedItemInfos:
        return cachedItemInfos[key]
    info = itemComp.GetItemBasicInfo(itemName, auxValue, isEnchanted=isEnchanted)
    cachedItemInfos[key] = info
    return info


axe_items_cache = {} #存储物品是否为axe类别结果的字典


def isAxe(itemName, auxValue=0):
    """
    判断给定的物品是否为axe类型并将结果存储到字典中
    :param itemName: 物品名称
    :param auxValue: 附加值
    :return: True表示为axe类别，否则False
    """
    if itemName in axe_items_cache:
        return axe_items_cache[itemName]
    info = GetItemInfo(itemName, auxValue)
    if info and info["itemType"] == "axe":
        axe_items_cache[itemName] = True
        return True
    axe_items_cache[itemName] = False
    return False

def is_same_itme_ignore_count(old, new):
    """
    比较物品名、附加值、用户数据是否一致判断两个物品信息是否相同（忽略数量），
    :param old: 旧物品信息
    :param new: 新物品信息
    :return: True表示相同，否则False
    """
    if old["newAuxValue"] == new["newAuxValue"] and old["newItemName"] == new["newItemName"]:
        old_userData = old["userData"] if "userData" in old else None
        new_userData = new["userData"] if "userData" in new else None
        return old_userData == new_userData
    else:
        return False


def AddItemToPlayerInventory(playerId, spawnitem):
    '''
    给玩家背包发放物品，优先发放到背包，背包已满时，生成物品实体到脚下
    :param playerId: 玩家id
    :param spawnitem: 物品itemdict，count可以大于60
    :return:
    '''
    itemName = spawnitem["newItemName"]
    auxValue = spawnitem["newAuxValue"]
    count = spawnitem['count'] if 'count' in spawnitem else 0
    if count <= 0:
        return True
    info = itemComp.GetItemBasicInfo(itemName, auxValue)
    if info:
        maxStackSize = info['maxStackSize']
    else:
        maxStackSize = 1

    itemcomp = compFactory.CreateItem(playerId)
    playerInv = itemcomp.GetPlayerAllItems(ItemPosType.INVENTORY, True)

    for slotId, itemDict in enumerate(playerInv):
        if count > 0:
            if itemDict:
                if is_same_itme_ignore_count(itemDict, spawnitem):
                    canspawncount = maxStackSize - itemDict['count']
                    spawncount = min(canspawncount, count)
                    num = spawncount + itemDict['count']
                    itemcomp.SetInvItemNum(slotId, num)
                    count -= spawncount
            else:
                spawncount = min(maxStackSize, count)
                itemDict = deepcopy(spawnitem)
                itemDict['count'] = spawncount
                itemcomp.SpawnItemToPlayerInv(itemDict, playerId, slotId)
                count -= spawncount
        else:
            return True
    while count > 0:
        spawncount = min(maxStackSize, count)
        itemDict = deepcopy(spawnitem)
        itemDict['count'] = spawncount
        dim = compFactory.CreateDimension(playerId).GetEntityDimensionId()
        pos = compFactory.CreatePos(playerId).GetPos()
        pos = (pos[0], pos[1] - 1, pos[2])
        itemComp.SpawnItemToLevel(itemDict, dim, pos)
        count -= spawncount
    return True


def AddItemToContainer(chestpos, spawnitem, dimension=0):
    """
    先检查容器容量，若不足则返回False。
    利用is_same_itme_ignore_count判断槽位物品是否可叠加。
    优先往已有相同物品的槽位堆叠，没有则直接放入。
    最终返回是否成功放入物品。
    :param chestpos: 容器方块位置
    :param spawnitem: 要存入的物品信息字典
    :param dimension: 维度
    :return: True表示成功存入，否则存入失败
    """
    size = itemComp.GetContainerSize(chestpos, dimension)
    if size < 0:
        return False
    itemName = spawnitem["newItemName"]
    auxValue = spawnitem["newAuxValue"]
    count = spawnitem['count'] if 'count' in spawnitem else 0
    if count <= 0:
        return True
    info = itemComp.GetItemBasicInfo(itemName, auxValue)
    if info:
        maxStackSize = info['maxStackSize']
    else:
        maxStackSize = 1

    totalcanspawn = 0
    canspawnslotlist = []
    for slotId in range(size):
        if totalcanspawn < count:
            itemDict = itemComp.GetContainerItem(chestpos, slotId, dimension, getUserData=True)
            if itemDict:
                if is_same_itme_ignore_count(itemDict, spawnitem):
                    canspawncount = maxStackSize - itemDict['count']
                    if canspawncount > 0:
                        totalcanspawn += canspawncount
                        canspawnslotlist.append([slotId, canspawncount])
            else:
                totalcanspawn += maxStackSize
                canspawnslotlist.append([slotId, maxStackSize])
        else:
            break
    if totalcanspawn < count:
        return False

    spawnResult = False
    for slotId, canspawncount in canspawnslotlist:
        if count > 0:
            itemDict = itemComp.GetContainerItem(chestpos, slotId, dimension, getUserData=True)
            if not itemDict:
                itemDict = deepcopy(spawnitem)
                itemDict['count'] = 0
            spawncount = min(canspawncount, count)
            itemDict['count'] = spawncount + itemDict['count']
            r = itemComp.SpawnItemToContainer(itemDict, slotId, chestpos, dimension)
            if r:
                spawnResult = True
            count -= spawncount
        else:
            break
    return spawnResult
