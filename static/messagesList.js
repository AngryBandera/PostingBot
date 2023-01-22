let token = "1714618330:AAE8zVajugM5_WFcvkU8LKUQ0BFYTWjDXTI"

function createNew() {
    window.open("/dashboard", "_self")
}

function editMessage(message_id, mode) {
    window.open('/editMessagePage/' + message_id + '/' + mode, "_self")
}

function loadImgs(inst, id) {

    if (!inst.src.includes('telegram')) {
        fetch('https://api.telegram.org/bot' + token + '/getFile?file_id=' + id)
            .then(response => response.json())
            .then(data => {
                inst.src = 'https://api.telegram.org/file/bot' + token + '/' + data.result.file_path

            })
    }
}

function sendedList() {
    window.open('/messagesList', "_self")
}

function delayedList() {
    window.open('/messagesList/delayed', "_self")
}