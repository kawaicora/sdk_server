import SocketIOMaster from "/static/js/SocketIOMaster.js";

class PageManager {
    constructor() {
        this.pages = {};
        this.currentPage = "room";
        $(".bottom_nav a").on ("click", (event) => {
            this.SwitchPage(event.currentTarget.dataset.pageId)
        });
    }


    Hide(name){
        if ($(name).hasClass("hidden")){
            return;
        }
        $(name).addClass("hidden");
    }
    Show (name) {
        if (!$(name).hasClass("hidden")){
            return;
        }
        $(name).removeClass("hidden");
    }
    SwitchPage(pageId ) {
        $(".room_list_btn").removeClass("text-primary").addClass("text-gray-400 dark:text-gray-500");
        $(".text_chat_btn").removeClass("text-primary").addClass("text-gray-400 dark:text-gray-500");
        $(".voice_chat_btn").removeClass("text-primary").addClass("text-gray-400 dark:text-gray-500");
        $(".video_chat_btn").removeClass("text-primary").addClass("text-gray-400 dark:text-gray-500");
        $(".map_list_btn").removeClass("text-primary").addClass("text-gray-400 dark:text-gray-500");
        $(".my_page_btn").removeClass("text-primary").addClass("text-gray-400 dark:text-gray-500");
        this.Hide(".room-list-container");
        this.Hide(".video-chat-container");
        
        this.Hide(".text-chat-container");
        this.Hide(".voice-chat-container");
        this.Hide(".map-list-container");
        this.Hide(".my-page-container");

        

        this.currentPage = pageId;
        for (var i = 0 ;i < $(".bottom_nav a").length ;i++){
            let element = $(".bottom_nav a")[i];
            if(element.dataset.pageId== pageId) {
                 $(".content-title").html(element.innerHTML);
             $(".content-title span").css("font-weight","bold")
             $(".content-title span").css("font-size","16px !important")
            }
        }
        
    
        // 根据pageId显示对应的页面
        switch (pageId) {
            
            case "room_list":
                $(".room_list_btn").removeClass("text-gray-400 dark:text-gray-500").addClass("text-primary");
                this.Show(".room-list-container");
               
                break;
            case "video_chat":
                $(".video_chat_btn").removeClass("text-gray-400 dark:text-gray-500").addClass("text-primary");
                this.Show(".video-chat-container");
                break;
            case "text_chat":
                $(".text_chat_btn").removeClass("text-gray-400 dark:text-gray-500").addClass("text-primary");
                this.Show(".text-chat-container");
                break;
            case "voice_chat":
                $(".voice_chat_btn").removeClass("text-gray-400 dark:text-gray-500").addClass("text-primary");
                this.Show(".voice-chat-container");
                break;
            case "map_list":
                $(".map_list_btn").removeClass("text-gray-400 dark:text-gray-500").addClass("text-primary");
                this.Show(".map-list-container");
                break;
            
            case "my_page":
                $(".my_page_btn").removeClass("text-gray-400 dark:text-gray-500").addClass("text-primary");
                this.Show(".my-page-container");
                break;
            
            default:
                console.error(`Unknown pageId: ${pageId}`);
        }
    }
}

export default new PageManager();