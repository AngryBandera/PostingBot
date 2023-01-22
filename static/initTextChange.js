import emojis from './emojis.json' assert { type: 'json' };
const emoji_data = emojis['emojis']

export let changed = false

function setCookie(cname, cvalue, exdays) {
    let d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    let expires = "expires=" + d.toUTCString();
    document.cookie = cname + "=" + cvalue + "; " + expires;
}

$(document).ready(function() {
    let editor = new FroalaEditor('#intro', {
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
                changed = true
                let text = $("#intro").val()

                setCookie('text', text, 30)
            },
        }
    }, function() {
        editor.html.set($('#msg_data').data()['other']['text']);
    });
})