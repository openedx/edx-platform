var _certificates = function (data) {
    this.data = data;
    this.init = function () {
        this.c = document.getElementById("canvas");
        this.ctx = this.c.getContext("2d");
        this.username = data.username;
        this.course = data.course;
        this.course_id = data.course_id;
        this.dateTime = data.dateTime;
        this.date = data.date;
        this.verifyTitle = data.verifyTitle;
        this.verifyAdress = data.verifyAdress;
        this.getImgSource();
        this.draw();
    }
    this.getImgSource = function () {
        this.bg = document.querySelector('#bg');
        this.qrcode = document.querySelector('#qrcode img');
        this.list = document.querySelectorAll('.signature');
    }
    this.draw = function () {
        var ctx = this.ctx;
        ctx.drawImage(this.bg, 0, 0, 1170, 826);
        ctx.drawImage(this.qrcode, 134, 614, 78, 78);

        ctx.textBaseline = 'top';
        ctx.fillStyle = '#434a54'
        ctx.font = "400 36px 'Open Sans','Helvetica Neue',Helvetica,Arial,sans-serif";
        ctx.fillText(this.username, 137, 307);
        ctx.fillStyle = '#205179';
        // 英文判断
        if (course.length > 36){
            ctx.font = "400 30px 'Open Sans','Helvetica Neue',Helvetica,Arial,sans-serif";
        }else{
            ctx.font = "400 38px 'Open Sans','Helvetica Neue',Helvetica,Arial,sans-serif";
        }
        ctx.fillText(this.course, 137, 424);
        ctx.font = "400 18px 'Open Sans','Helvetica Neue',Helvetica,Arial,sans-serif";
        ctx.fillText(this.course_id, 137, 476);
        ctx.fillStyle = '#434a54';
        ctx.font = "400 12px 'Open Sans','Helvetica Neue',Helvetica,Arial,sans-serif";
        ctx.fillText(this.dateTime, 221, 621);
        ctx.fillText(this.date, 221, 638);
        ctx.fillStyle = '#b0b0b0';
        ctx.fillText(this.verifyTitle, 221, 660);
        ctx.fillText(this.verifyAdress, 221, 678);
        // 画签名
        this.drawSignature();
        var imgDom = this.convertCanvasToImage(c);
        document.getElementById('container').appendChild(imgDom);
    }
    this.drawSignature = function () {
        var list = this.list;
        var ctx = this.ctx;
        ctx.fillStyle = '#434a54';
        ctx.font = "400 14px 'Open Sans','Helvetica Neue',Helvetica,Arial,sans-serif";
        var top = 626;
        for (var i = 0, len = list.length; i < len; i++) {
            ctx.fillStyle = '#434a54';
            var IMG = this.list[i];
            var textWidth = ctx.measureText(IMG.name)
            ctx.drawImage(IMG, 921, top - i * 85, 114, 50);
            ctx.fillText(IMG.name, 900 - textWidth.width, top + 20 - i * 85);
            ctx.fillStyle = '#ededed';
            ctx.fillRect(921, top + 57 - i * 85, 115, 2);
        }
    }
    this.convertCanvasToImage = function () {
        var image = new Image();
        image.src = canvas.toDataURL("image/png");
        return image;
    }
    this.init();
}