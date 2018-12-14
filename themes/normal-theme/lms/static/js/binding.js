var phoneDialog = function(){
    (function(){
        var all = 0;
        var timer = null;
        var clock = function(){
        if (all >= 0){
            $('.get-qrcode-btn').html(all);
            all -= 1;
        } else {
            clearInterval(timer);
            all = 0;
            $('.get-qrcode-btn').html(gettext('获取验证码'));
            $('.get-qrcode-btn').addClass('active');
        }
        }
        var checkPhone = function(phone){
        if (phone == ''){
            return gettext('手机号不能为空')
        } else if(!(/^(13[0-9]|14[56789]|15[0-9]|16[56]|17[0-9]|18[0-9]|19[89])\d{8}$/.test(phone))){
            return gettext('手机号格式不正确')
        } else{
            return true;
        }
        }
        var _eventHandle = function(){
        $('.get-qrcode-btn').click(function(){
            if($(this).hasClass('active')){
            // 检验手机号码
            //
            var phone = $('.phone-input-box').val();
            console.log(phone)
            if(checkPhone(phone) !== true){
                $('.error-text').addClass('active');
                $('.error-text').html(checkPhone(phone));
                $('.phone-number').addClass('error');
                return;
            }
            $('.phone-number').removeClass('error');
            $('.error-text').removeClass('active');
            $(this).removeClass('active');          
            $.ajax({
                url: '/api/user/v1/accounts/send_code_binding_phone/',
                type: 'post',
                data: {
                phone: phone,
                },
                headers : {'Authorization': $.cookie('csrftoken')},
                success: function(){
                all = 60;
                clock()
                timer = setInterval(clock, 1000);
                },
                error: function(error){
                console.log(error)
                $('.error-text').addClass('active');
                $('.error-text').html(error.responseText);
                }
            });
            }

        });
        $('.phone-input-box').bind("input propertychange", function(){
            var phone = $('.phone-input-box').val();
            if(phone == '' || phone.length != 11){
            $('.get-qrcode-btn').removeClass('active');
            } else if (all == 0){
            $('.get-qrcode-btn').addClass('active');
            }
        })
        $('.qrcode-input-box').bind("input propertychange", function(){
            console.log('1231')
            var phone = $('.phone-input-box').val();
            var code = $(this).val();
            if (checkPhone(phone) == true && code != ''){
            $('.submit-btn').addClass('active');
            } else{
            $('.submit-btn').removeClass('active');
            }
        });
        $('.submit-btn').click(function(){
            
            if($(this).hasClass('active')){
            // 提交验证
            var phone = $('.phone-input-box').val();
            var code = $('.qrcode-input-box').val();
            $.ajax({
                url: '/api/user/v1/accounts/binding_phone/',
                type: 'post',
                data: {
                phone: phone,
                code: code,
                },
                headers : {'Authorization': $.cookie('csrftoken')},
                success: function(){
                console.log('绑定成功');
                $('.eliteu-message-box').show();
                $('.message-content').html(gettext('手机绑定成功'));
                $('.phone-dialog').hide();
                $('.meassage-op').hide();
                },
                error: function(error){
                console.log(error)
                $('.error-text').addClass('active');
                $('.error-text').html(error.responseText);
                }
            });
            }
        });
        // 关闭
        $('.fa-dialog-close').click(function(){
            $('.phone-dialog').hide();
        })
        }
        // 注册事件监听
        _eventHandle();
    })()
}