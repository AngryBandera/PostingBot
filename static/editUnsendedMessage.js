const buttonHtml = '<div class="buttonControl" id="btn"><div class="input-group mb-3"><input onfocusout="saveText(this)" name="{3}" type="text" class="form-control" placeholder="Твій текст" aria-label="Введи текст кнопки" id="textInput" value="{4}"><button onclick="delBtn(this)"><i class="material-icons">delete_forever</i></button></div><div class="form-check"><label class="form-check-label"><input type="radio" name="{0}" id="urlBtn" onclick="stateChanged(this)" value="urlBtn">Повідомлення з посиланням</label><label class="radio-inline"> <input type="radio" name="{1}" id="emojiBtn" onclick="stateChanged(this)" value="emojiBtn" checked>Повідомлення з нативним коментарем</label></div><div id="dataInput" class="input-group mb-3" style="display:None"><input onfocusout="saveText(this)" type="text" id="dataInput" name="{2}" class="form-control" placeholder="Твоє посилання" aria-label="Твоє посилання" value="{5}"></div></div>'

const service_id = "-1001713538957"
const token = "1714618330:AAE8zVajugM5_WFcvkU8LKUQ0BFYTWjDXTI"
let imgs = []
let buttons = []
let imgsChanged = false
let crnt_img_file = undefined
let initText = $('#msg_data').data()['other']['text']

let isDelayed = false
let disable_web_preview = false

let msg_data = $('#msg_data').data()['other'];
let msg = $('#msg').data()['other'];

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

function setCookie(cname, cvalue, exdays) {
    let d = new Date();
    d.setTime(d.getTime() + (exdays * 24 * 60 * 60 * 1000));
    let expires = "expires=" + d.toUTCString();
    document.cookie = cname + "=" + cvalue + "; " + expires;
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
    d.className = 'btn_'
    row.appendChild(d);
    if (id != 0) { $(row).children("#addBtn")[0].remove() }

    if (id <= 1) {
        let btn = document.createElement("button");
        btn.className = 'btn btn-outline-secondary'
        btn.id = "addBtn"
        btn.style = 'height:40px'
        btn.innerHTML = '<i class="material-icons">add_circle</i>'
        btn.setAttribute("onClick", "addButton(false, this);");

        $(row)[0].appendChild(btn);
    }
    setCookie('buttons', JSON.stringify(buttons), 30)

    return row
}

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
        for (const element of result.value) {
            let inst = element
            let img = document.createElement('img')
            img.src = URL.createObjectURL(inst)
            for (let i = 0; i < 11; i++) {
                let used = false
                imgs.forEach((imgO) => {
                    if (imgO.id == i) {
                        used = true
                    }
                })
                if (!used) {
                    img.id = i;
                    break
                }
            }
            img.id = imgs.length
            img.onclick = function() {
                imgs.splice(this.id, 1)
                this.remove()
                console.log(imgs);
            }
            imgsChanged = true
            imgs.push({ img: inst, id: parseInt(img.id) })
            $(".imgsContainer").append(img)
        }
    })
}

function parseText(text) {
    text = text.replaceAll('&nbsp', ' ')
    return text
}

function PublishChanges() {

    let chat_id = msg.chat_id
    let reply_markup = { "inline_keyboard": [] }
    let text = getCookie('text')
    if (text == '') {
        text = initText
    }

    let formData = new FormData();
    disable_web_preview = $('#web_preview_check').is(":checked")
    console.log(disable_web_preview);

    text = parseText(text)

    imgs = imgs.sort((a, b) => a.id - b.id);
    console.log(text)
    formData.append('text', text)
    formData.append('message_id', msg_data['message_id'])
    formData.append('token', token)
    formData.append('chat_id', chat_id)
    formData.append('db_id', msg.id)
    formData.append('isDelayChanged', isDelayed)
    formData.append('isImgsChanged', imgsChanged)
    formData.append('disable_web_preview', disable_web_preview)

    let rowN = 0
    let emojiId = 0
    let unfilled_info
    buttons.forEach((row) => {

        let rowK = []
        let column = 0
        unfilled_info = false
        row.forEach((button) => {
            let textb = button['text']
            let url = button['data']
            if (text == "" || (url == "" && button['type'] == "url")) {
                Swal.fire({
                    icon: 'error',
                    title: 'Помилка',
                    text: 'В одній з кнопок є незаповнена інформація',
                })
                unfilled_info = true
            }
            if (button['type'] == "url") rowK.push({ "url": url, "text": textb })
            else {
                rowK.push({ "callback_data": `${rowN}|${column}|0|${textb}|-1|${emojiId}`, "text": textb + " 0" })
                emojiId++
            }
            column++
        })
        reply_markup["inline_keyboard"].push(rowK)

        rowN++
    })

    if (unfilled_info) {
        console.log("Unfilled info")
        return
    }
    formData.append('reply_markup', JSON.stringify(reply_markup));

    let i = 0
    console.log(imgs);
    imgs.forEach(function(img) {
        if (img['local'] != false) formData.append(`local${i}`, img['img'])
        else formData.append(img['file_id'], img['img'])
        i++
    })

    if (isDelayed) {
        let time = $('#timeInput').val()
        formData.append("time", time)
    }

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

    request.open('POST', '/editUnsendedMessage');
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
                inst.id = imgs.length
                inst.onclick = function() {
                    imgs.splice(this.id, 1)
                    this.remove()
                    console.log(imgs);
                }
                fetch(src)
                    .then(res => res.blob())
                    .then(blob => {

                        let file = new File([blob], 'telegram_image', { type: blob.type, });
                        imgs.push({ img: file, id: parseInt(inst.id), file_id: id, local: false })
                        console.log(imgs);
                    });
            })
    }
}

function delayStateChanged(inst) {
    isDelayed = $(inst).is(":checked")
    if ($(inst).is(":checked"))
        $("#timeContainer")[0].style.display = null;
    else
        $("#timeContainer")[0].style.display = "none";
}

function stateChanged(inpt) {
    let Ttype = 'url'
    if (inpt.value == 'emojiBtn') {
        $(inpt).parent().parent().parent().children("#dataInput")[0].style.display = "none";
        Ttype = "emoji"
    } else $(inpt).parent().parent().parent().children("#dataInput")[0].style.display = null;

    let nums = [parseInt(inpt.name.split('|')[1]), parseInt(inpt.name.split('|')[0])]
    let btn = buttons[nums[0]][nums[1]]
    btn['type'] = Ttype
    buttons[nums[0]][nums[1]] = btn
}

function saveText(field) {
    let row = field.name.split("|")[1]
    let num = field.name.split("|")[0]

    row = parseInt(row)
    num = parseInt(num)

    let btn = buttons[row][num]
    btn[field.id.substring(0, 4)] = field.value
    buttons[row][num] = btn
    setCookie('buttons', JSON.stringify(buttons), 30)
}

function deleteButton(element) {
    parent = $(element).parent().parent().parent()
    let i = 0
    buttons.forEach(function(button) {
        if (button['id'] == parent.attr('id')) {
            buttons.splice(i);
            setCookie('buttons', JSON.stringify(buttons), 30)
            parent.remove()
            return
        }

        i++
    })
}

function delBtn(btn) {
    let field = $(btn).parent().children("#textInput")[0]

    let row = field.name.split("|")[1]
    let num = field.name.split("|")[0]

    row = parseInt(row)
    num = parseInt(num)
    console.log(buttons);
    console.log(buttons[row].length);
    if (buttons[row].length == 3) {
        let btnNew = document.createElement("button");
        btnNew.className = 'btn btn-outline-secondary'
        btnNew.id = "addBtn"
        btnNew.style = 'height:40px'
        btnNew.innerHTML = '<i class="material-icons">add_circle</i>'
        btnNew.setAttribute("onClick", "addButton(false, this);");
        $(btn).parent().parent().parent().parent()[0].appendChild(btnNew);
    } else if (buttons[row].length == 1) {
        $(btn).parent().parent().parent().parent().find(addBtn).remove()
        buttons.splice(row, 1)
    } else buttons[row].splice(num, 1)
        // btnData = buttons[row].splice(num, 1)
    $(btn).parent().parent().parent()[0].remove()

    setCookie('buttons', JSON.stringify(buttons), 30)
}