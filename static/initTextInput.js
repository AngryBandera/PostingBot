import emojis from './emojis.json' assert { type: 'json' };
const emoji_data = emojis['emojis']

var inited = false

function setCookie(cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    var expires = "expires=" + d.toUTCString();
    document.cookie = cname + "=" + cvalue + "; " + expires;
}

function getCookie(cname) {
    var name = cname + "=";
    var ca = document.cookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

$(document).ready(function() {
    var editor = new FroalaEditor('#intro', {
        toolbarButtons: [
            ['undo', 'redo', 'bold', 'italic', 'underline', 'strikeThrough', 'insertLink', 'emoticons']
        ],
        emoticonsUseImage: false,
        quickInsertEnabled: false,
        language: 'uk',
        emoticonsStep: 4,
        emoticonsSet: emoji_data,
        events: {
            'charCounter.update': function() {
                var text = $("#intro").val()
                if (text == '' && !inited) return
                setCookie('text', text, 30)
            },
        }
    }, function() {
        editor.html.set(getCookie('text'));
        inited = true;
    });
})