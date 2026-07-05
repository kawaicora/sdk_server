# -*- coding: utf-8 -*-
import inspect
from app.utils.LoggerManager import logger
import os
import threading
import time

from lupa import LuaRuntime

class ScriptLib:

    def __init__(self,lua_runtime:LuaRuntime,lua_path):

        self.logger = logger
        from gameservice.gameserver import GameServer
        self.telegram_bot = GameServer.inst().telegram_bot
        self.lua:LuaRuntime = lua_runtime
        self.lua_path = lua_path
        self.define_lua_functions()
    
    def print_caller_info(enabled=True):
        def decorator(func):
            def wrapper(*args, **kwargs):
                if enabled:
                    # 获取调用栈信息
                    stack = inspect.stack()
                    # stack[1] 表示调用当前函数的栈帧
                    caller_frame = stack[1]
                    caller_module = inspect.getmodule(caller_frame[0])
                    caller_name = caller_frame[3]

                    if caller_module:
                        caller_module_name = caller_module.__name__
                    else:
                        caller_module_name = "unknown"

                    logging.info(f"调用来自 {caller_module_name} 模块的 {caller_name} 方法")

                # 调用原始函数
                result = func(*args, **kwargs)
                return result

            return wrapper

        return decorator

    def define_lua_functions(self):
        from gameservice.gameserver import GameServer
        # 将 Python 函数暴露给 Lua 环境
        self.lua.globals().ScriptLib = {
            "PrintCallInfo":self.print_call_info,
            "PrintContextLog": self.print_context_log,
            "GetRunFlag":self.get_run_flag,
            "SleepSec":self.sleep_sec,
            "TelegramBotGetChatId":GameServer.inst().telegram_bot.get_chat_id,
            "TelegramBotSetChatId":GameServer.inst().telegram_bot.set_chat_id,
            "TelegramBotSendMessage":GameServer.inst().telegram_bot.send_message,
            
        }
                # Generate the Lua script
        lua_script = self.generate_lua_script(self.lua.globals().ScriptLib)
        
        # Save or print the Lua script
        with open(os.path.join(self.lua_path,"generated_lua_script.lua"), "w") as f:
            f.write(lua_script)
        
        logging.info("Lua script has been generated.")

    def generate_lua_script(self, functions_dict):
        lua_script = "local ScriptLib = {}\n"

        for func_name, func in functions_dict.items():
            # Get function signature and parameters from the Python function
            signature = inspect.signature(func)
            params = signature.parameters
            param_names = list(params.keys())
            param_docs = [f"-- @param {param} {param}" for param in param_names]
            return_type = "void"  # Default return type is void
            
            # For simplicity, assuming that return type is void or not specified
            # You can extend this to deduce return types if needed

            # Create Lua function definition and comment
            lua_script += f"-- {func_name} function\n"
            lua_script += "\n".join(param_docs) + "\n"
            lua_script += f"function ScriptLib.{func_name}({', '.join(param_names)})\n"
            lua_script += f"    -- Function implementation\n"
            lua_script += f"end\n\n"
        lua_script += "return ScriptLib"
        return lua_script

    def sleep_sec(self,sec):
        time.sleep(sec)
    def get_run_flag(self):
        return True
    def print_context_log(self,context,msg):
        self.logger.info(f"{context} : {msg}")
        return
    def print_call_info(self):
        # 使用 Lua 的 debug.getinfo 函数获取调用栈信息
        get_info = self.lua.eval('debug.getinfo(3, "Sln")')
        short_src = get_info['short_src']
        func_name = get_info['name']
        line_num = get_info['currentline']

        log_msg = f"来自 {short_src} 文件的 {func_name or '匿名函数'} 方法（第 {line_num} 行）"
        self.logger.info(log_msg)
    