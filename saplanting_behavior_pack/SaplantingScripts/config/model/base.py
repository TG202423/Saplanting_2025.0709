# -*- coding: utf-8 -*-
# @Time    : 2023/7/24 11:13
# @Author  : taokyla
# @File    : base.py
class BaseConfig(object):
    """
    配置基类，提供基本的配置属性管理功能。
    支持将配置对象转成字典（dump）、从字典加载数据（load_data）、重置为默认值（reset）、属性读取（get）、属性设置（set）。
    """
    def dump(self):
        """
        将当前配置对象转成字典形式。
        如果属性值是BaseConfig的子类，则递归调用其dump()方法进行转换。
        只导出不以下划线开头的属性。
        返回一个字典，键是属性名，值是对应属性值（或其dump结果）。
        """
        return dict((k, v.dump() if isinstance(v, BaseConfig) else v) for k, v in self.__dict__.iteritems() if not k.startswith("_"))

    def load_data(self, data):
        """
        用字典data中的数据更新当前配置对象。
        遍历data的每个键值对，如果对象本身有该属性，则赋值。
        如果属性是BaseConfig的子类，则递归调用load_data加载子对象。
        """
        for key in data:
            if hasattr(self, key):
                value = getattr(self, key)
                if isinstance(value, BaseConfig):
                    value.load_data(data[key])
                else:
                    setattr(self, key, data[key])

    def reset(self):
        """
        重置配置为类定义中的默认值。
        遍历实例属性，若该属性在类定义中存在，则用类定义的值覆盖实例的当前值。
        """
        for key in self.__dict__:
            if key in self.__class__.__dict__:
                self.__dict__[key] = self.__class__.__dict__[key]

    def get(self, key, default=None):
        """
        读取属性值，若属性不存在则返回默认值default。
        """
        if key in self.__dict__:
            return self.__dict__[key]
        return default

    def set(self, key, value):
        """
        设置属性值，前提是属性存在。
        """
        if key in self.__dict__:
            setattr(self, key, value)


class SavableConfig(BaseConfig):
    """
    继承BaseConfig，增加保存（save）和加载（load）接口，
    供具体子类实现持久化配置的读取和存储。
    """
    _KEY = "config_data_key"

    def load(self):
        """
        读取配置数据，供子类实现。
        """
        raise NotImplementedError

    def update_config(self, config):
        """
        传入配置字典，调用load_data更新当前对象，再调用save持久化保存。
        """
        self.load_data(config)
        self.save()

    def save(self):
        """
        保存配置数据，供子类实现。
        """
        raise NotImplementedError