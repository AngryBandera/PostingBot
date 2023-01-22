const buttonHtml = '<div class="buttonControl" id="btn"><div class="input-group mb-3" style="margin-top:1em"><input readonly="readonly" type="text" class="form-control" placeholder="Твій текст" aria-label="Введи текст кнопки" id="textInput" value="{4}"></div></div>'
const imgHtml = '<div id="imgDiv"></div>'

const service_id = "-1001713538957"
let token = "1714618330:AAE8zVajugM5_WFcvkU8LKUQ0BFYTWjDXTI"
let buttons = []
let imgsChanged = false
let imgs = []
let crnt_img_file = undefined
let crnt_img = undefined

let msg_data = $('#msg_data').data()['other'];
let msg = $('#msg').data()['other'];
let disable_web_preview = false

String.prototype.format = function() {
    let args = arguments;
    return this.replace(/{(\d+)}/g, function(match, index) {
        return typeof args[index] == 'undefined' ? match : args[index];
    });
};

$(document).ready(function() {
    let buttonsCookie = msg_data['reply_markup']

    if (buttonsCookie['inline_keyboard'] != "") {
        buttonsCookie['inline_keyboard'].forEach(function(row) {
            let rowInst = null
            row.forEach(function(button) {
                if (button['callback_data'] != null) {
                    button['text'] = button['text'].slice(0, -2)
                }
                if (button == null) return
                if (rowInst == null) rowInst = addButton(true, null, button['text'], button['callback_data'], true)
                else addButton(false, rowInst, button['text'], button['callback_data'], true)
            })
        })
    } else buttons = []
})

function addImage() {
    Swal.fire({
        title: 'Вибери фотографію',
        input: 'file',
        inputAttributes: {
            'accept': 'image/*',
            'aria-label': 'Завантаж фотографію',
            'multiple': 'multiple'
        }
    }).then((result) => {
        if (result.value.length == 0) return
        imgsChanged = true
        for (const element of result.value) {
            let inst = element
            crnt_img_file = inst
            let img = document.createElement('img')
            img.src = URL.createObjectURL(inst)
            img.id = imgs.length

            crnt_img.remove()
            crnt_img = img
            $(".imgsContainer").append(img)
                // imgs.push({ img: inst, id: imgs.length, local: true })
        }
    })
}

function getCookie(cname) {
    let name = cname + "=";
    let ca = document.cookie.split(';');
    for (const element of ca) {
        let c = element;
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

function addButton(orientation, inst = null, text = "", data = "", fromCookie = false) {
    // orientation = True => new row
    let container = document.getElementById("buttonsContainer");
    let rowNum, row
    if (orientation) {
        if (buttons.length == 3) return

        buttons.push([])
        let row_inst = document.createElement("div");
        row_inst.className = 'btn_row'
        row_inst.id = `row${(buttons.length - 1).toString()}`
        rowNum = buttons.length - 1
        container.appendChild(row_inst);
        row = $(container).children("#" + row_inst.id)[0]
    } else {
        if (fromCookie) row = inst
        else row = $(inst).parent()[0]
        rowNum = row.id.replace("row", "")
    }

    let d = document.createElement("div");
    let id = Object.keys(buttons[rowNum]).length
    let btn_id = `${id.toString()}|${rowNum}`
    d.id = "btn" + btn_id
    d.innerHTML = buttonHtml.format(btn_id, btn_id, btn_id, btn_id, text, data)
    buttons[rowNum][id] = { text: text, data: data, type: "emoji", id: id }
    d.className = "btn_"

    row.appendChild(d);

    return row
}

function parseText(text) {
    text = text.replaceAll('&nbsp', ' ')
    return text
}

function PublishChanges() {

    let chat_id = msg.chat_id

    let text = $("#intro").val()
    text = parseText(text)

    let formData = new FormData();


    imgs = imgs.sort((a, b) => a.id - b.id);

    formData.append('text', text)
    formData.append('group', msg_data['group'])
    formData.append('media', msg_data['media'])
    formData.append('message_id', msg_data['message_id'])
    formData.append('token', token)
    formData.append('chat_id', chat_id)
    formData.append('db_id', msg.id)
    formData.append('disable_web_preview', disable_web_preview)


    if (!msg_data['group']) formData.append('local', crnt_img_file)

    let request = new XMLHttpRequest();

    request.addEventListener("load", function() {});

    request.onreadystatechange = function() {
        if (this.readyState == 4) {
            if (JSON.parse(this.responseText)['success']) {
                Swal.fire({
                    title: 'Повідомлення змінено',
                    icon: 'success'
                }).then((result) => {
                    MessagesList()
                })
            } else {
                Swal.fire({
                    title: 'Повідомлення не змінено',
                    text: 'Спробуй ще раз',
                    icon: 'error'
                })
            }
        }
    };

    let error_text

    // if (text == msg_data['text']) error_text = 'Ти не змінив текст повідомлення'
    if (text == "" && crnt_img == undefined) error_text = 'Ти не змінив текст повідомлення'
    else if (text == msg_data['text'] && crnt_img == undefined) error_text = 'Текст повідомлення не відрізняється'

    if (error_text) {
        Swal.fire({
            icon: 'error',
            title: 'Повідомлення не змінено',
            text: error_text,
            // footer: '<a href="">Why do I have this issue?</a>'
        })
        return
    }

    request.open('POST', '/editMessage');
    request.send(formData);

}

function MessagesList() {
    window.open("/messagesList", "_self")
}

function loadImgs(inst, id) {

    if (!inst.src.includes('telegram')) {
        fetch('https://api.telegram.org/bot' + token + '/getFile?file_id=' + id)
            .then(response => response.json())
            .then(data => {
                let src = 'https://api.telegram.org/file/bot' + token + '/' + data.result.file_path
                inst.src = src
                crnt_img = inst
                    // fetch(src)
                    //     .then(res => res.blob())
                    //     .then(blob => {

                //         let file = new File([blob], 'telegram_image', { type: blob.type, });
                //         imgs.push({ img: file, id: parseInt(inst.id), file_id: id, local: false })
                //     });
            })
    }
}

function webPreviewStateChanged(inst) {
    disable_web_preview = $(inst).is(":checked")
}