class CommonUtils {

    constructor(){

    }
    static inst (){

        if (!CommonUtils.instance){
            CommonUtils.instance = new CommonUtils();
        }
        return CommonUtils.instance;
    }
    // 静态方法，用于设置带有过期时间的cookie
    static SetCookieWithExpire(k, v, t) {
        // 创建一个新的Date对象，用于设置cookie的过期时间
        const date = new Date();
        // 将当前时间加上传入的过期时间（单位：毫秒）
        date.setTime(date.getTime() + t * 1000);
        // 将过期时间转换为UTC字符串格式
        const expires = "expires=" + date.toUTCString();
        // 设置cookie，格式为 键=值;过期时间
        document.cookie = k + "=" + v + ";" + expires + ";path=/";
    }

    // 静态方法，用于移除指定的cookie
    static RemoveCookie(k) {
        // 设置过期时间为过去的时刻
        const date = new Date();
        date.setTime(date.getTime() - 1);
        const expires = "expires=" + date.toUTCString();
        // 设置cookie的过期时间为过去，让浏览器自动删除它
        document.cookie = k + "=; " + expires + ";path=/";
    }

     // 静态方法，用于根据键获取对应的cookie值
    static GetCookie(k) {
        // 获取所有的cookie信息
        const name = k + "=";
        const ca = document.cookie.split(';');
        for (let i = 0; i < ca.length; i++) {
            let c = ca[i];
            // 去除cookie前面的空格
            while (c.charAt(0) === ' ') {
                c = c.substring(1);
            }
            // 判断当前cookie的键是否与传入的键匹配
            if (c.indexOf(name) === 0) {
                // 如果匹配，返回对应的cookie值
                return c.substring(name.length, c.length);
            }
        }
        // 如果没有找到匹配的cookie，返回空字符串
        return "";
    }

    
    static MsgBox(msg,showTime = 2000,aniTime = 500){

        var p_id = "msgbox"
        var s_id = "msgbox_"+parseInt(Math.random()*1000000 )
        var prent_box_code = `<div id="${p_id}" style="pointer-events: none;position:fixed;z-index:1000;display:flex;max-width:1000px;word-break:break-all;min-width: 100%;min-height: 100%;justify-items: center;justify-content: center;top:0px;left:0px;align-content: center;flex-direction: column;padding: 10px 10px;align-items: center;"></div>` 
        var msg_box_code = `<div id="${s_id}" style="z-index:1000; display:flex; opacity: 0;max-width:1000px; word-break:break-all; min-width: 400px;justify-items: center;justify-content: center;background:#00000071;border-radius: 10px;padding: 10px 10px;color: #FFFFFF;font-size: 24px;font-weight: 500; margin: 5px 0px;">
            </div>` 
        if($("#msgbox").length == 0){
            $("body").append(prent_box_code)
        }
        
        $("#msgbox").append(msg_box_code)
        $("#"+s_id+"").text(msg)
        var msg_box_height = $("."+s_id+"").height()
        var msg_box_width = $("."+s_id+"").width()
        $("#"+s_id+"").css({
            
            "margin-top":"-"+msg_box_height/2+"px",
            "margin-left":"-"+msg_box_width/2+"px",
            "top":"50%",
            "left":"50%"
        })
        $("#"+s_id+"").animate({opacity:1},aniTime)
        setTimeout(()=>{
            $("#"+s_id+"").animate({opacity:0},aniTime)
        },showTime)
        setTimeout(()=>{
            $("#"+s_id+"").remove()
        },showTime+aniTime*2+100)
    }
    
}

