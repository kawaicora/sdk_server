document.addEventListener('DOMContentLoaded', () => {


    function loadBackground(url) {

        document.body.setAttribute("style", `
            margin: 0;
            padding: 0;
            background-image: url(${url});
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
        `)

    }

    window.addEventListener('resize', function () {
        // 根据窗口大小重新加载背景图片
        const isHorizontal = window.innerWidth > window.innerHeight;
        if (isHorizontal) {
            loadBackground('/static/img/h_background.jpg');
        } else {
            loadBackground('/static/img/v_background.jpg');
        }
    });

    // 初始化，根据初始窗口大小加载背景图片
    if (window.innerWidth > window.innerHeight) {
        loadBackground('/static/img/h_background.jpg');
    } else {
        loadBackground('/static/img/v_background.jpg');
    }
})