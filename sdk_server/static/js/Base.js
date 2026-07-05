import SocketIOMaster from "/static/js/SocketIOMaster.js";
import LoggerManager from "/static/js/LoggerManager.js";

class Base{
    constructor(){
        this.logger = new LoggerManager("Base",LoggerManager.LEVELS.ALL)
        this.isLogined = false;
       
    }

    // 核心修改：改为POST，用请求体传递参数
    GetUserInfo(app_id, encrypted_login_token) {
        // 构建请求体数据
        const requestData = {};
        if (app_id !== null && encrypted_login_token !== null) {
            requestData.app_id = app_id;
            requestData.encrypted_login_token = encrypted_login_token;
        }

        $.ajax({
            url: "/api/v3/get_user_info",
            type: "POST", // 改为POST
            contentType: "application/json",
            data: JSON.stringify(requestData), // 序列化请求体
            success: (response)=> {
                

       
                if(response.retcode != 0){
                    $('.nav-user-login-btn').removeClass('hidden');
                    $('.exit-login-btn').addClass('hidden');
                    $('.nav-user-info').addClass('hidden');
                    this.logger.debug(`登陆失败 ${JSON.stringify( response, null, 2)}`);
                    return;
                }
                this.logger.debug(`登陆成功 ${JSON.stringify( response, null, 2)}`);
              

                $('.nav-user-login-btn').addClass('hidden');
                // $('.exit-login-btn').removeClass('hidden');
                $('.nav-user-info').removeClass('hidden');
                $('.nav-username').text(response.data.display_name);
                $(".nav-user-info a img")[0].src = response.data.avatar;
                this.isLogined = true;
                SocketIOMaster.connect();

     
                
            },
            error: (xhr, status, error) => {
                this.logger.error(`请求失败 ${JSON.stringify( error, null, 2)}`);
                SocketIOMaster.connect();
                
            }
        });
    }

    Logout(){
        CommonUtils.RemoveCookie("uid");
        location.href = "/view/login";
        $(".nav-user-info").addClass("hidden");
        $(".nav-user-login-btn").removeClass("hidden");

    }
    Login(account,password){

        // 这里可以添加表单验证和登录逻辑
        // this.logger.log(data.field.account);
        if(account == "" || password == ""){
            CommonUtils.MsgBox("用户名或密码不能为空！");
            return;
        }
        const encrypt = new JSEncrypt();

        
        $.ajax({
            url: "/api/get_password_public_key",
            type: "GET",
            contentType: "application/json",
            success: (response) => {
                this.logger.log(response);
                // 设置公钥
                encrypt.setPublicKey(response);
                var encrypted_pwd = encrypt.encrypt(password)

                $.ajax({
                    url: "/api/login",
                    type: "POST",
                    contentType: "application/json",
                    data: JSON.stringify({
                        account: account,
                        password: encrypted_pwd,
                        is_encrypt : true
                    }),
                    success: (response) => {
                        this.logger.log(response);
                        if(response.retcode == 0){
                            CommonUtils.MsgBox("登录成功!");
                            this.GetUserInfo();
                        }
                        else{
                            CommonUtils.MsgBox(`登录失败!  ${response.msg}`);

                        }
                    },
                    error: (xhr, status, error) => {
                        this.logger.error("Failed to send JSON data:", xhr.statusText);
                        CommonUtils.MsgBox(`登录失败! ${xhr.statusText}`);
                    }
                });
            },
            error:  (xhr, status, error) => {
                this.logger.error("Failed to send JSON data:", xhr.statusText);
                CommonUtils.MsgBox(`获取公钥失败! ${xhr.statusText}`);
            }
        });
    }
    SendVerifyCode(email,callback){
        $.ajax({
            url: "/api/send_verify_code",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({
                email:email
            }),
            success: (response,status,xhr) =>{
                if (response.retcode != 0 ){
                    CommonUtils.MsgBox(`发送验证码邮件失败! ${response.msg}`);
                    return;
                }
                var xTicket = xhr.getResponseHeader('X-Ticket');
                //获取header中的X-Ticket
                this.logger.log(response);
                callback(xTicket);
                CommonUtils.MsgBox("发送验证码邮件成功!");
            },
            error:  (xhr, status, error) =>{
                CommonUtils.MsgBox(`发送验证码邮件失败! ${xhr.statusText}`);
                this.logger.error("Failed to send JSON data:", xhr.statusText);
            }
        });
    }
    Register(account,password,username,avatar_url,phone_number,verify_code,xTicket){
        const encrypt = new JSEncrypt();
        
        $.ajax({
            url: "/api/get_password_public_key",
            type: "GET",
            contentType: "application/json",
            success: (response)  =>{
                this.logger.log(response);
                // 设置公钥
                encrypt.setPublicKey(response);
                var encrypted_pwd = encrypt.encrypt(password)
                $.ajax({
                    url: "/api/register",
                    type: "POST",
                    headers: {
                        "X-Ticket": xTicket
                    },
                    contentType: "application/json",
                    data: JSON.stringify({
                        avatar_url:avatar_url,
                        username:username,
                        phone_number:phone_number,
                        account:account,
                        password:encrypted_pwd,
                        verify_code:verify_code,
                        is_encrypt : true
                    }),
                    success: (response) =>{
                        this.logger.log(response);
                        if (response.retcode == 0){
                            CommonUtils.MsgBox("注册成功!")
                            location.href = "/view/login";
                        }else{
                            CommonUtils.MsgBox(`注册失败! ${response.msg}`)
                        }
                    },
                    error:  (xhr, status, error) => {
                        CommonUtils.MsgBox("注册失败!")
                        this.logger.error("Failed to send JSON data:", xhr.statusText);
                    }
                });
            },
            error:  (xhr, status, error) => {
                CommonUtils.MsgBox("获取公钥失败!");
                this.logger.error("Failed to send JSON data:", xhr.statusText);
            }
        });
    }
}

export default new Base();