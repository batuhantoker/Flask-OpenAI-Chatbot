(function () {
    var Message;
    Message = function (arg) {
        this.text = arg.text, this.message_side = arg.message_side;
        this.draw = function (_this) {
            return function () {
                var $message;
                $message = $($('.message_template').clone().html());
                $message.addClass(_this.message_side).find('.text').html(_this.text);
                $('.messages').append($message);
                return setTimeout(function () {
                    return $message.addClass('appeared');
                }, 0);
            };
        }(this);
        return this;
    };
    $(function () {
        var getMessageText, message_side, sendMessage;
        message_side = 'right';
        getMessageText = function () {
            var $message_input;
            $message_input = $('.message_input');
            return $message_input.val();
        };


        sendMessage = function (text) {
    var $messages, message;
    if (text.trim() === '') {
        return;
    }
    $('.message_input').val('');
    $messages = $('.messages');

    // Set message_side based on whether the message is from the user or chatbot
    var message_side = 'right';

    message = new Message({
        text: text,
        message_side: message_side
    });

// Draw user message
    message.draw();

// Call getResponse() to get the chatbot's response
$.get("/get", { msg: text }).done(function(data) {
    var botMessage = new Message({
        text: data,
        message_side: 'left'
    });


    // Draw bot message
    botMessage.draw();
    $messages.animate({ scrollTop: $messages.prop('scrollHeight') }, 300);
});

return $messages.animate({ scrollTop: $messages.prop('scrollHeight') }, 300);
};

        $('.send_message').click(function (e) {
            return sendMessage(getMessageText());
        });
        $('.message_input').keyup(function (e) {
            if (e.which === 13) {
                return sendMessage(getMessageText());
            }
        });
            // Add "Writing..." message
    var userId = $('#userInfo').data('userid');
    writingMessage = new Message({
        text: 'Hey, I am a ChatBot. I am designed to help you with identifying Spam and Phishing emails/sms. I support English and Spanish. Please feel free to ask me anything! Your UserID is ' + userId,
        message_side: 'left'
    });
    writingMessage.draw();

    });
}.call(this));
