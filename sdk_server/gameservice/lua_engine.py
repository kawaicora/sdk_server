# -*- coding: utf-8 -*-
import os
import logging
from lupa import LuaRuntime
from gameservice.lua_script_lib import *
from app.settings import DefaultConfig
class LuaEngine:
    
    def __init__(self):
        # 配置 logging 模块
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

        # 创建 Lua 运行时
        self.lua = LuaRuntime()
        # 获取 Lua 脚本所在的目录
        self.lua_script_dir = os.path.join(DefaultConfig.BASE_DIR, 'data', 'lua')

        self.lua_script_lib = ScriptLib(self.lua,self.lua_script_dir,logging)

        # 将 Lua 脚本目录添加到 Lua 的搜索路径中
        self.lua.execute(f'package.path = package.path .. ";{self.lua_script_dir.replace("\\", "/") }/?.lua"')
        self._initialized = True  # 标记已初始化
    def execute_script(self, script_name):
        try:
            # 构建脚本的完整路径
            script_path = os.path.join(self.lua_script_dir, script_name)
            if os.path.exists(script_path):
                # 读取脚本内容
                with open(script_path, 'r', encoding='utf-8') as file:
                    script_content = file.read()
                # 执行 Lua 脚本
                result = self.lua.execute(script_content)
                return result
            else:
                logging.info(f"脚本 {script_name} 不存在。")
        except Exception as e:
            logging.info(f"执行 Lua 脚本时出错: {e}")

    def get_lua_function(self, function_name):
        try:
            # 尝试获取 Lua 中的函数
            lua_function = self.lua.eval(function_name)
            if callable(lua_function):
                return lua_function
            else:
                logging.info(f"{function_name} 不是一个有效的 Lua 函数。")
        except Exception as e:
            logging.info(f"获取 Lua 函数时出错: {e}")
        return None

    def call_lua_function(self, function_name, *args):
        lua_function = self.get_lua_function(function_name)
        if lua_function:
            try:
                result = lua_function(*args)
                return result
            except Exception as e:
                logging.info(f"调用 Lua 函数 {function_name} 时出错: {e}")
        return None
    def load_all_lua_scripts(self):
        try:
            # 遍历目录下的所有文件
            for root, dirs, files in os.walk(self.lua_script_dir):
                for file in files:
                    if file.endswith('.lua'):
                        script_path = os.path.join(root, file)
                        with open(script_path, 'r', encoding='utf-8') as f:
                            script_content = f.read()
                            self.lua.execute(script_content)
        except Exception as e:
            logging.info(f"加载 Lua 脚本{script_path}出错: {e}")


if __name__ == "__main__":
    lua_env = LuaEngine()
